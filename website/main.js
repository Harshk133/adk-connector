(function () {
  "use strict";

  var PART_NAMES = [
    "ring_blue", "ring_green", "face", "eye_left", "eye_right",
    "plane", "plane_fold", "bracket", "chevron_left", "chevron_right",
  ];
  var CAPSULE = ["ring_blue", "ring_green", "face", "eye_left", "eye_right", "plane", "plane_fold"];
  var LOWER_ROW = ["bracket", "chevron_left", "chevron_right"];

  // Each part offset is [x, y, z, rotX, rotY, rotZ, dim].
  function dimmed(names, amount) {
    var result = {};
    names.forEach(function (name) { result[name] = [0, 0, 0, 0, 0, 0, amount]; });
    return result;
  }

  function merge() {
    return Object.assign.apply(Object, [{}].concat(Array.prototype.slice.call(arguments)));
  }

  // Moves pieces out of a chapter so that it has one clear subject.
  function away(names, x, y, z) {
    var result = {};
    names.forEach(function (name) { result[name] = [x, y, z, 0.3, 0.5, 0, 0.6]; });
    return result;
  }

  // group is [rotX, rotY, rotZ, scale, focusX, focusY].
  var POSES = {
    hero: { group: [0.1, -0.42, 0.03, 1.02, 0, 0], parts: {} },
    wrap: {
      group: [0.08, 0.42, -0.04, 1, 0, 0],
      parts: {
        bracket: [-0.12, -0.12, 0.25, 0, 0.2, 0, 0],
        chevron_left: [-0.08, -0.12, 0.42, 0, 0.3, 0, 0],
        chevron_right: [0.14, -0.12, 0.42, 0, -0.3, 0, 0],
      },
    },
    channels: {
      group: [0.12, -0.26, 0.03, 1.02, 0.05, 1.05],
      parts: merge(dimmed(["ring_blue", "ring_green", "face", "eye_left", "eye_right"], 0.5), away(LOWER_ROW, 0, -3.4, -0.5), {
        plane: [-0.72, 0.98, 0.95, 0.22, -0.32, 0.16, 0],
        plane_fold: [-0.75, 0.93, 0.85, 0.22, -0.32, 0.16, 0],
      }),
    },
    multi: {
      group: [0.08, 0.26, 0, 0.92, 0, 0.83],
      parts: merge(away(LOWER_ROW, 0, -3.4, -0.5), {
        ring_blue: [-0.58, 0, 0, 0, 0.28, 0, 0],
        ring_green: [0.62, 0, 0, 0, -0.28, 0, 0],
        plane: [0.62, 0, 0.1, 0, -0.28, 0, 0],
        plane_fold: [0.62, 0, 0.1, 0, -0.28, 0, 0],
        face: [0, 0, 0.55, 0, 0, 0, 0],
        eye_left: [0, 0, 0.72, 0, 0, 0, 0],
        eye_right: [0, 0, 0.72, 0, 0, 0, 0],
      }),
    },
    streaming: {
      group: [-0.08, -0.32, 0, 1.08, 0.42, -1.15],
      parts: merge(away(CAPSULE, 0, 4.6, -1), away(["bracket"], -3.6, 0, -0.5), {
        chevron_left: [-0.16, 0, 0.62, 0, 0.5, 0, 0],
        chevron_right: [0.26, 0, 0.62, 0, -0.5, 0, 0],
      }),
    },
    voice: {
      group: [0.06, 0.2, 0, 1.18, -0.2, 0.83],
      parts: merge(away(LOWER_ROW, 0, -3.4, -0.5), dimmed(["ring_green", "plane", "plane_fold"], 0.62), {
        ring_blue: [0, 0, -0.1, 0, 0, 0, 0.3],
        face: [0, 0, 0.36, 0, 0, 0, 0],
        eye_left: [0, 0, 0.62, 0, 0, 0, 0],
        eye_right: [0, 0, 0.62, 0, 0, 0, 0],
      }),
    },
    sessions: {
      group: [0.1, -0.18, 0, 0.94, -0.15, 1.05],
      parts: merge(away(LOWER_ROW, 0, -3.4, -0.5), dimmed(["ring_blue", "ring_green", "plane", "plane_fold"], 0.62), {
        face: [0, 0, 0, 0, 0, 0, 0.25],
        eye_left: [-0.2, 1.38, 0.62, 0.15, 0.3, 0, 0],
        eye_right: [0.2, 1.38, 0.62, 0.15, -0.3, 0, 0],
      }),
    },
    tunnel: {
      group: [0.14, 0.36, 0.02, 1.32, -1.3, -1.15],
      parts: merge(away(CAPSULE, 0, 4.8, -1), away(["chevron_left", "chevron_right"], 4.2, -0.5, -0.5), {
        bracket: [0.12, 0.05, 0.7, 0.22, 0.3, 1.57, 0],
      }),
    },
    agents: {
      group: [0.1, -0.26, 0, 0.82, 0, 0.72],
      parts: {
        bracket: [0.3, 3.72, 0.55, 0.2, 0.5, 0.3, 0],
        chevron_left: [-0.95, 0.12, 0.7, 0, 0.5, -0.2, 0],
        chevron_right: [0.42, 3.52, 0.55, 0.2, -0.5, 0.3, 0],
      },
    },
    pipeline: {
      group: [0.2, 0.92, 0.05, 0.94, 0, 0],
      parts: {
        ring_blue: [0, 0, -1.3, 0, 0, 0, 0],
        ring_green: [0, 0, -0.85, 0, 0, 0, 0],
        face: [0, 0, 0, 0, 0, 0, 0],
        eye_left: [0, 0, 0.55, 0, 0, 0, 0],
        eye_right: [0, 0, 0.55, 0, 0, 0, 0],
        plane_fold: [0, 0, 0.85, 0, 0, 0, 0],
        plane: [0, 0, 1.25, 0, 0, 0, 0],
        bracket: [0, 0, -1.3, 0, 0, 0, 0],
        chevron_left: [0, 0, 0.1, 0, 0, 0, 0],
        chevron_right: [0, 0, 1.25, 0, 0, 0, 0],
      },
    },
    extend: {
      group: [0.08, -0.32, 0, 0.98, 0.2, 0.55],
      parts: merge(away(LOWER_ROW, 0, -3.8, -0.5), {
        ring_green: [0.98, -0.72, 0.8, 0.18, -0.5, -0.22, 0],
        plane: [0.98, -0.72, 0.9, 0.18, -0.5, -0.22, 0],
        plane_fold: [0.98, -0.72, 0.9, 0.18, -0.5, -0.22, 0],
        ring_blue: [0, 0, 0, 0, 0, 0, 0.3],
        face: [0, 0, 0, 0, 0, 0, 0.3],
        eye_left: [0, 0, 0, 0, 0, 0, 0.3],
        eye_right: [0, 0, 0, 0, 0, 0, 0.3],
      }),
    },
    install: { group: [0.08, Math.PI * 2 - 0.34, 0, 1.02, 0, 0], parts: {} },
  };

  var TINTS = {
    blue: { base: [10, 21, 48], glow: [74, 136, 239] },
    green: { base: [6, 33, 27], glow: [61, 163, 87] },
    red: { base: [42, 15, 18], glow: [235, 69, 55] },
    yellow: { base: [36, 26, 7], glow: [250, 175, 8] },
  };

  var GROUP_SIZE = 6;
  var PART_SIZE = 7;
  var POSE_SIZE = GROUP_SIZE + 1 + PART_NAMES.length * PART_SIZE;
  var MOBILE_WIDTH = 820;

  var stage = document.getElementById("stage");
  var canvas = document.getElementById("logo-canvas");
  var progressBar = document.getElementById("progress-bar");
  var sections = Array.prototype.slice.call(document.querySelectorAll("[data-pose]"));
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function clamp(value, low, high) { return Math.min(high, Math.max(low, value)); }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function smoother(t) { return t * t * t * (t * (t * 6 - 15) + 10); }

  function flattenPose(section) {
    var pose = POSES[section.dataset.pose];
    var side = section.classList.contains("copy-left") ? 1 : -1;
    var flat = new Float32Array(POSE_SIZE);
    pose.group.forEach(function (value, i) { flat[i] = value; });
    flat[GROUP_SIZE] = side;
    PART_NAMES.forEach(function (name, i) {
      (pose.parts[name] || []).forEach(function (value, j) {
        flat[GROUP_SIZE + 1 + i * PART_SIZE + j] = value;
      });
    });
    return flat;
  }

  var keyframes = sections.map(function (section) {
    return { element: section, pose: flattenPose(section), tint: TINTS[section.dataset.tint], anchor: 0, side: section.classList.contains("copy-left") ? 1 : -1 };
  });

  function measureAnchors() {
    var viewport = window.innerHeight;
    keyframes.forEach(function (key) {
      var rect = key.element.getBoundingClientRect();
      var top = rect.top + window.scrollY;
      key.anchor = Math.max(0, top + rect.height / 2 - viewport / 2);
    });
    keyframes[0].anchor = 0;
    var last = keyframes[keyframes.length - 1];
    last.anchor = Math.min(last.anchor, document.documentElement.scrollHeight - viewport);
  }

  // Returns the two neighbouring keyframes around the scroll position and the blend between them.
  function locate(scroll) {
    var index = 0;
    while (index < keyframes.length - 2 && scroll >= keyframes[index + 1].anchor) index += 1;
    var from = keyframes[index];
    var to = keyframes[index + 1];
    var raw = clamp((scroll - from.anchor) / Math.max(to.anchor - from.anchor, 1), 0, 1);
    var held = clamp((raw - 0.16) / 0.68, 0, 1);
    return { from: from, to: to, t: reducedMotion ? Math.round(raw) : smoother(held) };
  }

  var scrollTarget = new Float32Array(POSE_SIZE);

  function updateFromScroll() {
    var scroll = window.scrollY;
    var limit = document.documentElement.scrollHeight - window.innerHeight;
    progressBar.style.transform = "scaleX(" + clamp(scroll / Math.max(limit, 1), 0, 1) + ")";

    var place = locate(scroll);
    for (var i = 0; i < POSE_SIZE; i += 1) scrollTarget[i] = lerp(place.from.pose[i], place.to.pose[i], place.t);

    var base = [0, 1, 2].map(function (c) { return Math.round(lerp(place.from.tint.base[c], place.to.tint.base[c], place.t)); });
    var glow = [0, 1, 2].map(function (c) { return Math.round(lerp(place.from.tint.glow[c], place.to.tint.glow[c], place.t)); });
    stage.style.setProperty("--tint", "rgb(" + base.join(",") + ")");
    stage.style.setProperty("--glow", "rgba(" + glow.join(",") + ",0.34)");
    if (window.innerWidth > MOBILE_WIDTH) {
      stage.style.setProperty("--glow-x", lerp(26, 74, (lerp(place.from.side, place.to.side, place.t) + 1) / 2) + "%");
    } else {
      stage.style.removeProperty("--glow-x");
    }
    updateTypedReply();
  }

  // Streaming chapter: the bot's reply is written as the reader scrolls through it.
  var typedSection = document.getElementById("streaming");
  var typedText = document.querySelector("[data-typed]");
  var typedCount = document.querySelector("[data-typed-count]");
  var fullReply = typedText.textContent;

  function updateTypedReply() {
    if (reducedMotion) return;
    var rect = typedSection.getBoundingClientRect();
    var progress = clamp((window.innerHeight * 0.7 - rect.top) / (rect.height * 0.55), 0, 1);
    var length = Math.round(fullReply.length * progress);
    typedText.textContent = fullReply.slice(0, Math.max(length, 1));
    typedCount.textContent = String(length);
  }

  // Copy buttons
  document.querySelectorAll("[data-copy]").forEach(function (button) {
    var label = button.querySelector("[data-copy-label]");
    button.addEventListener("click", function () {
      function done(message) {
        label.textContent = message;
        window.setTimeout(function () { label.textContent = "Copy"; }, 1600);
      }
      if (!navigator.clipboard) { selectCommand(button); done("Select"); return; }
      navigator.clipboard.writeText(button.dataset.copy).then(
        function () { done("Copied"); },
        function () { selectCommand(button); done("Select"); }
      );
    });
  });

  function selectCommand(button) {
    var range = document.createRange();
    range.selectNodeContents(button.querySelector("code"));
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }

  var scrollQueued = false;
  window.addEventListener("scroll", function () {
    if (scrollQueued) return;
    scrollQueued = true;
    window.requestAnimationFrame(function () { scrollQueued = false; updateFromScroll(); });
  }, { passive: true });

  function refreshLayout() { measureAnchors(); updateFromScroll(); }
  window.addEventListener("resize", refreshLayout);
  window.addEventListener("load", refreshLayout);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(refreshLayout);
  measureAnchors();
  updateFromScroll();

  startScene();

  function startScene() {
    if (!window.THREE || !THREE.GLTFLoader || !THREE.RoomEnvironment) return;

    var renderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
    } catch (error) {
      return;
    }

    var isSmall = window.innerWidth <= MOBILE_WIDTH;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isSmall ? 1.75 : 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.LinearToneMapping;
    renderer.toneMappingExposure = 0.7;
    renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = !isSmall;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    var scene = new THREE.Scene();
    var environment = new THREE.PMREMGenerator(renderer);
    scene.environment = environment.fromScene(new THREE.RoomEnvironment(), 0.04).texture;
    environment.dispose();

    var camera = new THREE.PerspectiveCamera(30, 1, 0.1, 60);
    camera.position.z = 11;

    var key = new THREE.DirectionalLight(0xffffff, 1.15);
    key.position.set(-3.5, 5, 7);
    key.castShadow = !isSmall;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.camera.left = -5;
    key.shadow.camera.right = 5;
    key.shadow.camera.top = 5;
    key.shadow.camera.bottom = -5;
    key.shadow.camera.far = 24;
    key.shadow.normalBias = 0.025;
    key.shadow.radius = 5;
    scene.add(key);

    var pivot = new THREE.Group();
    scene.add(pivot);

    var parts = [];
    var current = new Float32Array(POSE_SIZE);
    current.set(scrollTarget);

    function resize() {
      var width = canvas.clientWidth;
      var height = canvas.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
    new ResizeObserver(resize).observe(canvas);
    resize();

    var pointerX = 0;
    var pointerY = 0;
    var easedX = 0;
    var easedY = 0;
    if (!reducedMotion && window.matchMedia("(pointer: fine)").matches) {
      window.addEventListener("pointermove", function (event) {
        pointerX = event.clientX / window.innerWidth - 0.5;
        pointerY = event.clientY / window.innerHeight - 0.5;
      }, { passive: true });
    }

    function applyPose(time) {
      var viewHeight = 2 * camera.position.z * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      var viewWidth = viewHeight * camera.aspect;
      var small = window.innerWidth <= MOBILE_WIDTH;
      var fit;
      var centerX;
      var centerY;
      if (small) {
        fit = Math.min(viewWidth / 3.95, (viewHeight * 0.37) / 4.1);
        centerX = 0;
        centerY = viewHeight * 0.245;
      } else {
        fit = Math.min((viewWidth * 0.46) / 3.9, (viewHeight * 0.82) / 4.1);
        centerX = current[GROUP_SIZE] * viewWidth * 0.245;
        centerY = 0;
      }

      var float = reducedMotion ? 0 : Math.sin(time * 0.0006);
      pivot.position.set(centerX, centerY + float * 0.04, 0);
      pivot.rotation.set(
        current[0] + easedY * 0.14,
        current[1] + easedX * 0.24 + float * 0.045,
        current[2]
      );
      pivot.scale.setScalar(fit * current[3]);

      var model = pivot.children[0];
      model.position.set(-current[4], -current[5], 0);

      parts.forEach(function (part, i) {
        var offset = GROUP_SIZE + 1 + i * PART_SIZE;
        part.mesh.position.set(
          part.origin.x + current[offset],
          part.origin.y + current[offset + 1],
          part.origin.z + current[offset + 2]
        );
        part.mesh.rotation.set(current[offset + 3], current[offset + 4], current[offset + 5]);
        part.material.color.copy(part.baseColor).multiplyScalar(1 - current[offset + 6] * 0.78);
      });
    }

    var lastTime = performance.now();
    function frame(time) {
      var delta = Math.min(time - lastTime, 64);
      lastTime = time;
      var follow = reducedMotion ? 1 : 1 - Math.exp(-delta * 0.0075);
      for (var i = 0; i < POSE_SIZE; i += 1) current[i] += (scrollTarget[i] - current[i]) * follow;
      easedX += (pointerX - easedX) * 0.05;
      easedY += (pointerY - easedY) * 0.05;
      applyPose(time);
      renderer.render(scene, camera);
      window.requestAnimationFrame(frame);
    }

    new THREE.GLTFLoader().load("assets/adk-connector-logo.glb", function (gltf) {
      var model = gltf.scene;
      pivot.add(model);
      PART_NAMES.forEach(function (name) {
        var mesh = model.getObjectByName(name);
        var material = mesh.material.clone();
        mesh.material = material;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        parts.push({ mesh: mesh, material: material, baseColor: material.color.clone(), origin: mesh.position.clone() });
      });
      window.requestAnimationFrame(function (time) {
        lastTime = time;
        frame(time);
        stage.classList.add("ready");
      });
    });
  }
})();
