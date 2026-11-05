import * as THREE from './vendor/three.module.js';
import { PointerLockControls } from './vendor/PointerLockControls.js';

const MODULES = [
  {id: 'bd', title: 'MÓDULO 1 · ACCESO', concept: 'Inyección SQL', color: 0x31d7ff},
  {id: 'programacion', title: 'MÓDULO 2 · MEMORIA', concept: 'Desbordamiento de búfer', color: 0xffb347},
  {id: 'vulnerabilidades', title: 'MÓDULO 3 · CREDENCIALES', concept: 'Autenticación débil', color: 0xff4d8d},
];

let camera, renderer, controls, scene, clock;
let paused = true;
let interactables = [];
let keys = new Set();
let prompt;
let hasStarted = false;

function makeMaterial(color, emissive = color) {
  return new THREE.MeshStandardMaterial({color, emissive, emissiveIntensity: 0.35, roughness: 0.7});
}

function addBox(parent, size, position, color, emissive = color) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), makeMaterial(color, emissive));
  mesh.position.set(...position);
  parent.add(mesh);
  return mesh;
}

function createScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070b1c);
  scene.fog = new THREE.Fog(0x070b1c, 18, 85);
  scene.add(new THREE.HemisphereLight(0x7895ff, 0x100b23, 1.4));

  const cyan = new THREE.PointLight(0x2ddcff, 18, 18);
  cyan.position.set(-4, 3.2, 0);
  scene.add(cyan);
  const magenta = new THREE.PointLight(0xff267f, 16, 20);
  magenta.position.set(4, 3.2, -42);
  scene.add(magenta);

  addBox(scene, [12, 0.2, 82], [0, -0.15, -33], 0x111936, 0x172b6a);
  addBox(scene, [0.2, 4, 82], [-6, 1.8, -33], 0x161b38, 0x08184d);
  addBox(scene, [0.2, 4, 82], [6, 1.8, -33], 0x161b38, 0x08184d);
  addBox(scene, [12, 0.2, 82], [0, 4, -33], 0x10142b, 0x22104d);

  for (let z = 2; z > -72; z -= 8) {
    addBox(scene, [0.12, 0.08, 2.2], [-3.6, 0.02, z], 0x36e0ff, 0x36e0ff);
    addBox(scene, [0.12, 0.08, 2.2], [3.6, 0.02, z], 0xff2b9a, 0xff2b9a);
  }

  MODULES.forEach((module, index) => {
    const z = -15 - index * 19;
    const door = addBox(scene, [3.6, 3.1, 0.18], [0, 1.55, z], 0x182444, module.color);
    door.userData = {type: 'door', module, z};
    interactables.push(door);
    addBox(scene, [0.12, 3.4, 0.12], [-1.85, 1.7, z], module.color, module.color);
    addBox(scene, [0.12, 3.4, 0.12], [1.85, 1.7, z], module.color, module.color);
    const terminal = addBox(scene, [1.2, 1.1, 0.35], [3.9, 0.85, z + 2], 0x12223b, module.color);
    terminal.userData = {type: 'terminal', module};
    interactables.push(terminal);
    addBox(scene, [1.4, 0.08, 0.2], [3.9, 1.45, z + 1.8], module.color, module.color);
    const label = makeLabel(`${module.title}\n${module.concept}`, module.color);
    label.position.set(-4.3, 2.9, z + 0.1);
    scene.add(label);
    const hologram = addBox(scene, [1.4, 2.1, 0.08], [-3.7, 1.15, z - 2], 0x11223a, module.color);
    hologram.material.transparent = true;
    hologram.material.opacity = 0.55;
    hologram.userData = {type: 'enemy', module};
  });
}

function makeLabel(text, color) {
  const canvas = document.createElement('canvas');
  canvas.width = 700;
  canvas.height = 160;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#071021';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = `#${color.toString(16).padStart(6, '0')}`;
  ctx.lineWidth = 6;
  ctx.strokeRect(4, 4, canvas.width - 8, canvas.height - 8);
  ctx.fillStyle = '#e8f4ff';
  ctx.font = 'bold 28px monospace';
  text.split('\n').forEach((line, index) => ctx.fillText(line, 22, 58 + index * 42));
  const texture = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, transparent: true}));
  sprite.scale.set(4.2, 0.96, 1);
  return sprite;
}

function isRepaired(module) {
  return Boolean(window.cyberQuestState?.modules?.[module.id]);
}

function nearestInteractable() {
  let nearest = null;
  let distance = 2.8;
  interactables.forEach(item => {
    const current = camera.position.distanceTo(item.position);
    if (current < distance) {
      nearest = item;
      distance = current;
    }
  });
  return nearest;
}

function updatePrompt() {
  const target = nearestInteractable();
  if (!target || paused) {
    prompt.classList.add('hidden');
    return;
  }
  const {module, type} = target.userData;
  const locked = type === 'door' && module.id !== 'bd' && !isRepaired(MODULES[MODULES.findIndex(item => item.id === module.id) - 1]);
  document.getElementById('fpPromptText').textContent = locked
    ? `🔒 ${module.title}: repara el módulo anterior`
    : `Presiona E para ${type === 'terminal' ? 'usar la terminal' : 'abrir el módulo'}`;
  prompt.classList.remove('hidden');
}

function isBlocked(position) {
  return interactables.some(item => {
    if (item.userData.type !== 'door') return false;
    const index = MODULES.findIndex(module => module.id === item.userData.module.id);
    const locked = index > 0 && !isRepaired(MODULES[index - 1]);
    return locked && Math.abs(position.z - item.position.z) < 0.8 && Math.abs(position.x) < 2;
  });
}

function interact() {
  const target = nearestInteractable();
  if (!target) return;
  const {module, type} = target.userData;
  const index = MODULES.findIndex(item => item.id === module.id);
  const locked = type === 'door' && index > 0 && !isRepaired(MODULES[index - 1]);
  if (locked) {
    document.getElementById('fpPromptText').textContent = '🔒 El programador debe reparar el módulo anterior primero.';
    return;
  }
  if (module.id === 'bd') window.openSqlEditor?.();
  else if (module.id === 'programacion') window.openFirstPersonChallenge?.('buffer');
  else window.openFirstPersonChallenge?.('auth');
}

function movePlayer(delta) {
  if (paused) return;
  const direction = new THREE.Vector3();
  if (keys.has('KeyW')) direction.z -= 1;
  if (keys.has('KeyS')) direction.z += 1;
  if (keys.has('KeyA')) direction.x -= 1;
  if (keys.has('KeyD')) direction.x += 1;
  if (!direction.lengthSq()) return;
  direction.normalize().multiplyScalar(5 * delta);
  const next = controls.object.position.clone().add(direction);
  next.x = THREE.MathUtils.clamp(next.x, -5.2, 5.2);
  next.z = THREE.MathUtils.clamp(next.z, -77, 5);
  if (!isBlocked(next)) controls.object.position.copy(next);
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(clock.getDelta(), 0.05);
  movePlayer(delta);
  updatePrompt();
  renderer.render(scene, camera);
}

function showPause() {
  paused = !controls.isLocked;
  document.getElementById('fpOverlay').classList.toggle('hidden', !paused);
  document.getElementById('fpStart').classList.toggle('hidden', hasStarted);
  document.getElementById('fpPause').classList.toggle('hidden', !hasStarted || !paused);
}

function startFirstPerson() {
  const container = document.getElementById('game');
  container.innerHTML = '';
  renderer = new THREE.WebGLRenderer({antialias: true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setClearColor(0x070b1c, 1);
  renderer.shadowMap.enabled = true;
  container.style.background = '#070b1c';
  container.appendChild(renderer.domElement);
  renderer.domElement.style.position = 'absolute';
  renderer.domElement.style.inset = '0';
  renderer.domElement.style.zIndex = '0';
  camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.1, 100);
  camera.position.set(0, 1.65, 4);
  controls = new PointerLockControls(camera, renderer.domElement);
  scene = new THREE.Scene();
  createScene();
  scene.add(controls.object);
  clock = new THREE.Clock();
  prompt = document.getElementById('fpPrompt');
  document.getElementById('fpInteract').onclick = interact;
  document.getElementById('fpStart').onclick = () => {
    hasStarted = true;
    paused = false;
    document.getElementById('fpOverlay').classList.add('hidden');
    controls.lock();
    setTimeout(() => {
      if (hasStarted && !controls.isLocked) {
        paused = false;
        document.getElementById('fpOverlay').classList.add('hidden');
      }
    }, 500);
  };
  controls.addEventListener('lock', () => { paused = false; showPause(); });
  controls.addEventListener('unlock', () => { paused = true; showPause(); });
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
  window.addEventListener('keydown', event => {
    if (event.code === 'KeyE' || event.key?.toLowerCase() === 'e') {
      event.preventDefault();
      interact();
    }
    if (event.code.startsWith('Key') || event.code.startsWith('Arrow')) keys.add(event.code);
  });
  window.addEventListener('keyup', event => keys.delete(event.code));
  document.getElementById('fpPause').onclick = () => controls.lock();
  document.getElementById('fpOverlay').classList.remove('hidden');
  renderer.render(scene, camera);
  animate();
}

window.startFirstPerson = startFirstPerson;
