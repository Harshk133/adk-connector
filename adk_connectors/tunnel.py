import asyncio
import os
import re
import shutil
import logging
from typing import Optional

logger = logging.getLogger("adk_connectors.tunnel")

class CloudflareTunnel:
    def __init__(self, port: int, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.proc: Optional[asyncio.subprocess.Process] = None
        self.public_url: Optional[str] = None

    async def _resolve_bin_path(self) -> str:
        bin_path = shutil.which("cloudflared")
        if bin_path:
            return bin_path
            
        import platform
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        filename = "cloudflared.exe" if system == "windows" else "cloudflared"
        local_dir = os.path.join(os.path.expanduser("~"), ".adk", "bin")
        local_path = os.path.join(local_dir, filename)
        
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return local_path

        # Determine OS name
        if system == "windows":
            os_name = "windows"
        elif system == "darwin":
            os_name = "darwin"
        elif system == "linux":
            os_name = "linux"
        else:
            raise RuntimeError(f"Unsupported operating system for auto-downloading cloudflared: {system}")

        # Determine ARCH name
        if machine in ("amd64", "x86_64"):
            arch_name = "amd64"
        elif machine in ("arm64", "aarch64"):
            arch_name = "arm64"
        else:
            arch_name = "amd64"

        download_filename = f"cloudflared-{os_name}-{arch_name}"
        if system == "windows":
            download_filename += ".exe"

        download_url = f"https://github.com/cloudflare/cloudflared/releases/latest/download/{download_filename}"

        logger.info(f"cloudflared binary not found on PATH. Downloading dynamically from {download_url}...")
        
        import httpx
        os.makedirs(local_dir, exist_ok=True)
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            async with client.stream("GET", download_url) as response:
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Failed to download cloudflared binary: HTTP {response.status_code}. "
                        "Please install cloudflared manually."
                    )
                with open(local_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
                        
        if system != "windows":
            os.chmod(local_path, 0o755)
            
        logger.info(f"cloudflared downloaded successfully to {local_path}")
        return local_path

    async def start(self) -> str:
        bin_path = await self._resolve_bin_path()
        logger.info(f"Starting cloudflared tunnel to http://{self.host}:{self.port} using {bin_path}...")
        
        self.proc = await asyncio.create_subprocess_exec(
            bin_path,
            "tunnel",
            "--url",
            f"http://{self.host}:{self.port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        
        async def find_url() -> Optional[str]:
            while True:
                line = await self.proc.stderr.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="ignore")
                match = url_regex.search(line_str)
                if match:
                    return match.group(0)
            return None

        try:
            url = await asyncio.wait_for(find_url(), timeout=15.0)
            if url:
                self.public_url = url
                logger.info(f"Cloudflare Tunnel created successfully: {self.public_url}")
                logger.info("Waiting 4 seconds for Cloudflare DNS propagation...")
                await asyncio.sleep(4.0)
                return self.public_url
        except asyncio.TimeoutError:
            await self.stop()
            raise RuntimeError("Timed out waiting for cloudflared to establish tunnel.")
        
        # If it finished early without error or URL
        await self.stop()
        raise RuntimeError("cloudflared closed before establishing a tunnel.")

    async def stop(self) -> None:
        if self.proc:
            logger.info("Stopping Cloudflare Tunnel...")
            try:
                self.proc.terminate()
                await asyncio.wait_for(self.proc.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                logger.warning("cloudflared process did not stop gracefully. Killing it...")
                self.proc.kill()
                await self.proc.wait()
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.error(f"Error terminating cloudflared: {e}")
            self.proc = None
            self.public_url = None


class NgrokTunnel:
    def __init__(self, port: int, authtoken: Optional[str] = None):
        self.port = port
        self.authtoken = authtoken
        self.public_url: Optional[str] = None

    async def start(self) -> str:
        try:
            from pyngrok import ngrok
        except ImportError:
            raise ImportError(
                "pyngrok package is required to use ngrok. Install it using 'pip install pyngrok'."
            )
        
        if self.authtoken:
            ngrok.set_auth_token(self.authtoken)
            
        loop = asyncio.get_running_loop()
        tunnel = await loop.run_in_executor(None, lambda: ngrok.connect(self.port))
        self.public_url = tunnel.public_url
        logger.info(f"ngrok Tunnel created successfully: {self.public_url}")
        return self.public_url

    async def stop(self) -> None:
        try:
            from pyngrok import ngrok
            if self.public_url:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: ngrok.disconnect(self.public_url))
        except Exception as e:
            logger.warning(f"Error closing ngrok tunnel: {e}")
        self.public_url = None
