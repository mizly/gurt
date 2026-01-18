// HUD Management Module

// Cache DOM elements
let hudOverlay = null;
let crosshair = null;
let ammoCount = null;
let maxAmmoDisplay = null;
let speedVal = null;
let speedBar = null;
let cooldownBar = null;
let muzzleFlash = null;

// State
let currentAmmo = 0;
let maxAmmo = 0;
let currentSpeed = 0;

export function initHUD() {
    hudOverlay = document.getElementById('hud-overlay');
    crosshair = document.querySelector('.hud-crosshair');
    ammoCount = document.getElementById('hud-ammo-count');
    maxAmmoDisplay = document.getElementById('hud-max-ammo');
    speedVal = document.getElementById('hud-speed-val');
    speedBar = document.getElementById('hud-speed-bar-fill');
    cooldownBar = document.getElementById('hud-cooldown-bar');
    muzzleFlash = document.querySelector('.muzzle-flash');
    enemyPanel = document.getElementById('hud-enemy-panel');
}

let lastFireTime = 0;
let cooldownDuration = 500; // ms
let enemyPanel = null;

export function updateHUD(gameState, inputState) {
    if (!hudOverlay) return;

    // 1. Update Ammo
    if (gameState.ammo !== undefined) {
        currentAmmo = gameState.ammo;
        maxAmmo = gameState.max_ammo || 30; // Default

        // Infer Cooldown based on Max Ammo (Class)
        // Vanguard (30) -> 500ms
        // Interceptor (60) -> 200ms
        // Juggernaut (10) -> 1000ms
        if (maxAmmo === 60) cooldownDuration = 200;
        else if (maxAmmo === 10) cooldownDuration = 1000;
        else cooldownDuration = 500;

        if (ammoCount) {
            ammoCount.textContent = currentAmmo.toString().padStart(2, '0');
            if (currentAmmo <= 5) ammoCount.classList.add('text-red-500');
            else ammoCount.classList.remove('text-red-500');
        }
        if (maxAmmoDisplay) maxAmmoDisplay.textContent = `/ ${maxAmmo}`;
    }

    // 2. Update Enemies
    if (gameState.enemies && enemyPanel) {
        if (enemyPanel.childElementCount !== gameState.enemies.length) {
            enemyPanel.innerHTML = gameState.enemies.map(e => `
                <div id="enemy-${e.id}" class="bg-black/50 backdrop-blur border border-white/10 rounded-lg p-1.5">
                    <div class="flex justify-between text-[8px] text-white/70 mb-0.5 font-mono">
                        <span class="enemy-id">${e.name}</span>
                        <span class="enemy-hp">${e.hp}/${e.max_hp}</span>
                    </div>
                    <div class="h-1 bg-white/10 rounded-full overflow-hidden">
                        <div class="enemy-bar h-full bg-red-500 transition-all duration-300" style="width: ${(e.hp / e.max_hp) * 100}%"></div>
                    </div>
                </div>
            `).join('');
        } else {
            gameState.enemies.forEach((e, i) => {
                const el = enemyPanel.children[i];
                if (el) {
                    const hpSpan = el.querySelector('.enemy-hp');
                    const bar = el.querySelector('.enemy-bar');
                    if (hpSpan) hpSpan.textContent = `${e.hp}/${e.max_hp}`;
                    if (bar) bar.style.width = `${(e.hp / e.max_hp) * 100}%`;
                }
            });
        }
    }

    // 2. Simulate Speedometer
    const forwardInput = (inputState.length !== undefined && inputState[1] !== undefined)
        ? Math.abs(inputState[1] - 127)
        : (inputState.axes ? Math.abs((inputState.axes[1] || 0) * 127) : 0);

    const turnInput = (inputState.length !== undefined && inputState[0] !== undefined)
        ? Math.abs(inputState[0] - 127)
        : (inputState.axes ? Math.abs((inputState.axes[0] || 0) * 127) : 0);
    const targetSpeed = Math.min((forwardInput + turnInput) / 1.2, 100);

    currentSpeed += (targetSpeed - currentSpeed) * 0.1;

    if (speedVal) speedVal.textContent = Math.floor(currentSpeed);
    if (speedBar) speedBar.style.width = `${Math.min(currentSpeed, 100)}%`;
}

export function attemptFire() {
    const now = Date.now();
    if (now - lastFireTime < cooldownDuration) return false;

    // Check if we have ammo (client-side prediction)
    if (currentAmmo <= 0) return false;

    lastFireTime = now;

    // Cooldown Animation
    if (cooldownBar) {
        // Reset to 0 with no transition
        cooldownBar.style.transition = 'none';
        cooldownBar.style.width = '0%';

        // Force reflow
        void cooldownBar.offsetWidth;

        // Animate to full
        cooldownBar.style.transition = `width ${cooldownDuration}ms linear`;
        cooldownBar.style.width = '100%';
    }

    triggerFireVFX();
    return true;
}

function triggerFireVFX() {
    if (muzzleFlash) {
        muzzleFlash.classList.remove('active');
        void muzzleFlash.offsetWidth; // Force reflow
        muzzleFlash.classList.add('active');

        const container = document.querySelector('.video-container');
        if (container) {
            container.animate([
                { transform: 'translate(0,0)' },
                { transform: 'translate(-2px, 2px)' },
                { transform: 'translate(1px, -1px)' },
                { transform: 'translate(0,0)' }
            ], {
                duration: 100,
                iterations: 1
            });
        }
    }
}
