// 1. Model Navigation Menu JavaScript - Cross-browser compatible approach
// Use window properties to prevent redeclaration errors on page reload
if (typeof window.isMenuToggling === 'undefined') {
    window.isMenuToggling = false; // Prevent rapid toggle/close cycles
}
if (typeof window.activeMenuTimeout === 'undefined') {
    window.activeMenuTimeout = null; // Track menu creation timing
}

function initializeModelNavigation() {
    console.log('🔧 Initializing model navigation...');

    // Add click listeners to all three-dot icons with capture phase for better Chrome compatibility
    document.addEventListener('click', handleDocumentClick, true);

    // Also add a non-capturing listener as fallback
    document.addEventListener('click', handleDocumentClickBubble, false);

    console.log('✅ Model navigation initialized successfully');
}

// Primary click handler (capture phase) - better for Chrome
function handleDocumentClick(e) {
    console.log('🖱️ Capture phase click on:', e.target);

    // Handle three-dot icon clicks
    if (e.target.closest('[anvil-role="icon-link-discreet"]')) {
        console.log('✅ Three-dot icon clicked (capture)!');
        e.preventDefault();
        e.stopImmediatePropagation(); // Stronger stop for Chrome

        handleThreeDotsClick(e);
        return;
    }

    // Handle individual option clicks
    if (e.target.closest('.option-icon')) {
        console.log('✅ Option icon clicked (capture)!');
        e.preventDefault();
        e.stopImmediatePropagation();

        handleOptionIconClick(e);
        return;
    }
}

// Secondary click handler (bubble phase) - fallback for Firefox
function handleDocumentClickBubble(e) {
    // Skip if we're in the middle of toggling a menu
    if (window.isMenuToggling) {
        console.log('🔄 Skipping bubble handler - menu is toggling');
        return;
    }

    // Only handle "click outside" logic in bubble phase
    if (!e.target.closest('.model-options-expanded') &&
        !e.target.closest('[anvil-role="icon-link-discreet"]') &&
        !e.target.closest('.option-icon')) {
        console.log('🔄 Closing all menus (clicked outside - bubble)');
        closeAllMenus();
    }
}

// Extract three-dots click handling
function handleThreeDotsClick(e) {
    let dotsLink = e.target.closest('[anvil-role="icon-link-discreet"]');
    if (!dotsLink) {
        dotsLink = findClosestByRole(e.target, 'icon-link-discreet');
        console.log('🧭 Fallback dotsLink by role scan:', dotsLink);
    }
    const modelId = resolveModelIdFromElement(dotsLink);
    // Robust container resolution
    let flowPanel = dotsLink.closest('[anvil-role="nav_flow_panel"]');
    if (!flowPanel) {
        flowPanel = dotsLink.closest('.flow-panel, .flow-panel-item, .anvil-container, .sidebar-elt, .content');
        console.log('🧭 Fallback flowPanel:', flowPanel);
    }

    console.log('📋 Model ID:', modelId);
    console.log('📋 Flow Panel:', flowPanel);

    if (flowPanel) {
        // Set toggle flag to prevent immediate close
        window.isMenuToggling = true;
        toggleModelOptions(flowPanel, modelId);
        // Clear flag after menu is established
        setTimeout(() => {
            window.isMenuToggling = false;
        }, 100);
    } else {
        console.warn('⚠️ Could not find a suitable container for options menu.');
    }
}

// Extract option icon click handling
function handleOptionIconClick(e) {
    const optionIcon = e.target.closest('.option-icon');
    const action = optionIcon.dataset.action;
    let modelId = optionIcon.dataset.modelId;
    if (!modelId) {
        // Fallback: read from parent expanded container or flow panel
        const expanded = optionIcon.closest('.model-options-expanded');
        if (expanded && expanded.dataset && expanded.dataset.modelId) {
            modelId = expanded.dataset.modelId;
            console.log('🔑 Fallback modelId via expanded container dataset:', modelId);
        }
    }
    if (!modelId) {
        const fp = optionIcon.closest('[anvil-role="nav_flow_panel"]');
        modelId = resolveModelIdFromElement(fp) || resolveModelIdFromElement(optionIcon);
        console.log('🔑 Fallback modelId via container/element resolve:', modelId);
    }

    console.log('📋 Action:', action, 'Model ID:', modelId);

    handleOptionClick(action, modelId);
}

// Helper: Walk up the DOM to find the nearest element with a specific anvil-role
function findClosestByRole(startEl, roleName) {
    let el = startEl;
    while (el) {
        const role = el.getAttribute && el.getAttribute('anvil-role');
        if (role === roleName) {
            return el;
        }
        el = el.parentElement;
    }
    return null;
}

// Helper: Resolve modelId from DOM element
function resolveModelIdFromElement(el) {
    if (!el) return null;
    // 1) tag attribute (if rendered)
    let id = el.getAttribute('tag');
    if (id) {
        console.log('🔑 Found modelId via tag attribute:', id);
        return id;
    }
    // 2) data-model-id on element
    if (el.dataset && el.dataset.modelId) {
        console.log('🔑 Found modelId via data-model-id on element:', el.dataset.modelId);
        return el.dataset.modelId;
    }
    // 3) from closest nav_flow_panel container
    const fp = el.closest('[anvil-role="nav_flow_panel"]');
    if (fp) {
        const fpTag = fp.getAttribute('tag');
        if (fpTag) {
            console.log('🔑 Found modelId via flow panel tag:', fpTag);
            return fpTag;
        }
        if (fp.dataset && fp.dataset.modelId) {
            console.log('🔑 Found modelId via flow panel data-model-id:', fp.dataset.modelId);
            return fp.dataset.modelId;
        }
        // 4) from model link inside container
        const link = fp.querySelector('[anvil-role*="model-nav-link"]');
        if (link) {
            const linkTag = link.getAttribute('tag');
            if (linkTag) {
                console.log('🔑 Found modelId via model link tag:', linkTag);
                return linkTag;
            }
            if (link.dataset && link.dataset.modelId) {
                console.log('🔑 Found modelId via model link data-model-id:', link.dataset.modelId);
                return link.dataset.modelId;
            }
        }
    }
    console.warn('⚠️ Could not resolve modelId from element.');
    return null;
}

// Helper: Find the flow panel (nav row) by modelId
function findFlowPanelByModelId(modelId) {
    if (!modelId) return null;
    // Try tag attribute
    let fp = document.querySelector(`[anvil-role="nav_flow_panel"][tag="${modelId}"]`);
    if (fp) return fp;
    // Try data-model-id
    fp = document.querySelector(`[anvil-role="nav_flow_panel"][data-model-id="${modelId}"]`);
    if (fp) return fp;
    // Fallback: iterate and compare
    const panels = document.querySelectorAll('[anvil-role="nav_flow_panel"]');
    for (const p of panels) {
        const t = p.getAttribute('tag') || (p.dataset && p.dataset.modelId);
        if (String(t) === String(modelId)) return p;
    }
    return null;
}

// Helper: pinned state
function isModelPinned(modelId) {
    const fp = findFlowPanelByModelId(modelId);
    return !!(fp && fp.classList.contains('pinned'));
}

// Helper: ensure a non-hover pin indicator exists at dots position
function ensurePinIndicator(flowPanel) {
    if (!flowPanel) return null;
    let indicator = flowPanel.querySelector('.pin-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'pin-indicator';
        indicator.innerHTML = '<i class="fa fa-thumb-tack"></i>';
        const gutter = flowPanel.querySelector('.flow-panel-gutter');
        if (gutter) {
            gutter.appendChild(indicator);
        } else {
            flowPanel.appendChild(indicator);
        }
    }
    return indicator;
}

function removePinIndicator(flowPanel) {
    if (!flowPanel) return;
    const indicator = flowPanel.querySelector('.pin-indicator');
    if (indicator) indicator.remove();
}

// Helper: notifications state
function isModelNotifyActive(modelId) {
    const fp = findFlowPanelByModelId(modelId);
    return !!(fp && fp.classList.contains('notify-active'));
}

// Helper: ensure a non-hover notify indicator exists at dots position
function ensureNotifyIndicator(flowPanel) {
    if (!flowPanel) return null;
    let indicator = flowPanel.querySelector('.notify-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'notify-indicator';
        indicator.innerHTML = '<i class="fa fa-bullhorn"></i>';
        const gutter = flowPanel.querySelector('.flow-panel-gutter');
        if (gutter) {
            gutter.appendChild(indicator);
        } else {
            flowPanel.appendChild(indicator);
        }
    }
    return indicator;
}

function removeNotifyIndicator(flowPanel) {
    if (!flowPanel) return;
    const indicator = flowPanel.querySelector('.notify-indicator');
    if (indicator) indicator.remove();
}

// Helper: Resort nav rows with FLIP animation (pinned first, then creation order)
function resortNavModels() {
    const panels = Array.from(document.querySelectorAll('[anvil-role="nav_flow_panel"]'));
    if (!panels.length) return;
    const parent = panels[0].parentElement;

    // 1) Record first positions
    const first = new Map();
    panels.forEach(p => {
        first.set(p, p.getBoundingClientRect());
    });

    // 2) Sort by pinned desc, then by data-order-index asc
    const sorted = panels.slice().sort((a, b) => {
        const ap = a.classList.contains('pinned');
        const bp = b.classList.contains('pinned');
        if (ap !== bp) return ap ? -1 : 1;
        const ai = parseInt(a.dataset.orderIndex || '0', 10);
        const bi = parseInt(b.dataset.orderIndex || '0', 10);
        return ai - bi;
    });

    // 3) Apply new order
    sorted.forEach(node => parent.appendChild(node));

    // 4) FLIP animate (robust: disable transition, set inverted transform, force reflow, then animate)
    sorted.forEach(node => {
        const last = node.getBoundingClientRect();
        const f = first.get(node);
        if (!f) return;
        const dx = f.left - last.left;
        const dy = f.top - last.top;
        if (dx || dy) {
            // a) Disable transitions and apply inverted transform
            node.style.transition = 'none';
            node.style.transform = `translate3d(${dx}px, ${dy}px, 0)`;

            // b) Force reflow so the browser commits the starting transform
            // eslint-disable-next-line no-unused-expressions
            node.getBoundingClientRect();

            // c) Enable transition and animate to the natural position
            node.style.transition = 'transform 1200ms cubic-bezier(0.25, 0.8, 0.25, 1)';
            node.style.transform = 'translate3d(0, 0, 0)';

            const cleanup = (e) => {
                if (e.propertyName === 'transform') {
                    node.style.transition = '';
                    node.removeEventListener('transitionend', cleanup);
                }
            };
            node.addEventListener('transitionend', cleanup);
        }
    });
}

// 2. Toggle model options display with improved Chrome compatibility
function toggleModelOptions(flowPanel, modelId) {
    console.log('🔄 Toggling model options for:', modelId);
    console.log('🔄 Flow panel:', flowPanel);

    // Clear any existing timeout
    if (window.activeMenuTimeout) {
        clearTimeout(window.activeMenuTimeout);
        window.activeMenuTimeout = null;
    }

    // Close other open menus first
    closeAllMenus();

    // Check if this panel already has expanded options
    let expandedContainer = flowPanel.querySelector('.model-options-expanded');
    console.log('🔍 Existing expanded container:', expandedContainer);

    if (!expandedContainer) {
        // Create the expanded options container
        if (!modelId) {
            modelId = resolveModelIdFromElement(flowPanel);
            console.log('🔑 Resolved modelId inside toggle from flowPanel:', modelId);
        }
        expandedContainer = createExpandedOptions(modelId);

        // Find the flow-panel-gutter to append to
        const gutter = flowPanel.querySelector('.flow-panel-gutter');
        console.log('🔍 Flow panel gutter:', gutter);
        if (gutter) {
            gutter.appendChild(expandedContainer);
            console.log('✅ Appended expanded container to gutter');
        } else {
            console.log('❌ No gutter found, appending to flow panel');
            flowPanel.appendChild(expandedContainer);
        }
    }

    // Add expanded class to flow panel and dots
    flowPanel.classList.add('expanded');
    console.log('✅ Added expanded class to flow panel');

    const dotsLink = flowPanel.querySelector('[anvil-role="icon-link-discreet"]');
    console.log('🔍 Dots link:', dotsLink);
    if (dotsLink) {
        dotsLink.classList.add('expanded');
        console.log('✅ Added expanded class to dots link');
    }

    // Ensure positioning context for absolute menu
    const currentPosition = getComputedStyle(flowPanel).position;
    if (currentPosition === 'static' || !currentPosition) {
        flowPanel.style.position = 'relative';
        console.log('🧭 Set flowPanel position: relative for menu positioning');
    }

    // Show the expanded container with improved timing for Chrome
    // Use requestAnimationFrame for better browser compatibility
    requestAnimationFrame(() => {
        expandedContainer.classList.add('active');
        console.log('✅ Added active class to expanded container');

        // Set a timeout to track when menu is fully established
        window.activeMenuTimeout = setTimeout(() => {
            console.log('📍 Menu fully established and stable');
            window.activeMenuTimeout = null;
        }, 350); // Slightly longer than CSS transition
    });
}

// 3. Create expanded options container
function createExpandedOptions(modelId) {
    console.log('🏗️ Creating expanded options for model:', modelId);

    const container = document.createElement('div');
    container.className = 'model-options-expanded';
    // propagate model id on container for fallback
    if (modelId != null) {
        container.dataset.modelId = modelId;
    }

    // Pin icon
    const pinIcon = createOptionIcon('fa-thumb-tack', 'pin', modelId, 'pin agent');

    // Megaphone icon
    const megaphoneIcon = createOptionIcon('fa-bullhorn', 'notifications', modelId, 'pin agent & activate notification');

    // Settings icon
    const settingsIcon = createOptionIcon('fa-sliders', 'settings', modelId, 'agent profile');

    // Trash icon
    const trashIcon = createOptionIcon('fa-trash', 'delete', modelId, 'delete agent');

    // Reflect pinned state in menu icon
    try {
        if (isModelPinned(modelId)) {
            pinIcon.classList.add('active');
        }
        if (isModelNotifyActive(modelId)) {
            megaphoneIcon.classList.add('active');
        }
    } catch (e) { /* noop */ }

    container.appendChild(pinIcon);
    container.appendChild(megaphoneIcon);
    container.appendChild(settingsIcon);
    container.appendChild(trashIcon);

    console.log('✅ Created expanded options container with 4 icons');
    return container;
}

// 4. Create individual option icon
function createOptionIcon(iconClass, action, modelId, title) {
    const option = document.createElement('div');
    option.className = 'option-icon';
    option.title = title;
    option.dataset.action = action;
    option.dataset.modelId = modelId;
    option.innerHTML = `<i class="fa ${iconClass}"></i>`;
    return option;
}

// 5. Handle option clicks
async function handleOptionClick(action, modelId) {
    console.log('Option clicked:', action, 'for model:', modelId);

    switch (action) {
        case 'settings':
            // Use Anvil's routing system instead of direct hash change
            if (typeof routing !== 'undefined' && routing.set_url_hash) {
                routing.set_url_hash(`model_profile?model_id=${modelId}&section=Main`, false);
            } else {
                // Fallback to direct hash change
                window.location.hash = `model_profile?model_id=${modelId}&section=Main`;
            }
            break;
        case 'pin': {
            const fp = findFlowPanelByModelId(modelId) || document.querySelector('[anvil-role="nav_flow_panel"].expanded');
            if (!fp) {
                console.warn('⚠️ No flow panel found to toggle pin');
                break;
            }
            const prevPinned = fp.classList.contains('pinned');
            const willPin = !prevPinned;

            // Optimistic UI update
            fp.classList.toggle('pinned', willPin);
            if (willPin) {
                ensurePinIndicator(fp);
            } else {
                removePinIndicator(fp);
            }
            const expanded = fp.querySelector('.model-options-expanded');
            if (expanded) {
                const pinOption = expanded.querySelector('.option-icon[data-action="pin"]');
                if (pinOption) pinOption.classList.toggle('active', willPin);
            }
            resortNavModels();

            // Persist on backend via MainIn bridge
            try {
                const formElement = document.querySelector('.anvil-container');
                if (!formElement || typeof anvil === 'undefined' || !anvil.call) {
                    console.warn('⚠️ Cannot call MainIn_update_agent_pin: anvil or form element missing');
                } else {
                    const res = await anvil.call(formElement, 'MainIn_update_agent_pin', parseInt(modelId, 10), willPin);
                    if (res !== 'success') throw new Error('Backend did not return success');
                }
            } catch (err) {
                console.error('❌ Error persisting pin state, rolling back:', err);
                // Rollback UI to previous state
                fp.classList.toggle('pinned', prevPinned);
                if (prevPinned) {
                    ensurePinIndicator(fp);
                } else {
                    removePinIndicator(fp);
                }
                const expanded2 = fp.querySelector('.model-options-expanded');
                if (expanded2) {
                    const pinOption2 = expanded2.querySelector('.option-icon[data-action="pin"]');
                    if (pinOption2) pinOption2.classList.toggle('active', prevPinned);
                }
                resortNavModels();
            }
            break;
        }
        case 'notifications': {
            const fp = findFlowPanelByModelId(modelId) || document.querySelector('[anvil-role="nav_flow_panel"].expanded');
            if (!fp) {
                console.warn('⚠️ No flow panel found to toggle notifications');
                break;
            }

            // Capture previous state for rollback
            const prevActive = fp.classList.contains('notify-active');
            const prevPinned = fp.classList.contains('pinned');
            const prevPinnedByNotify = fp.classList.contains('pinned-by-notify');

            const activating = !prevActive;
            // Optimistic UI update
            fp.classList.toggle('notify-active', activating);

            if (activating) {
                // Ensure notify indicator and pin behavior
                ensureNotifyIndicator(fp);
                // Replace any pin indicator with notify indicator
                removePinIndicator(fp);
                if (!fp.classList.contains('pinned')) {
                    fp.classList.add('pinned');
                    fp.classList.add('pinned-by-notify');
                }
                // Update menu highlight states
                const expanded = fp.querySelector('.model-options-expanded');
                if (expanded) {
                    const notifOption = expanded.querySelector('.option-icon[data-action="notifications"]');
                    if (notifOption) notifOption.classList.add('active');
                    const pinOption = expanded.querySelector('.option-icon[data-action="pin"]');
                    if (pinOption) pinOption.classList.toggle('active', fp.classList.contains('pinned'));
                }
            } else {
                // Deactivate notification and revert pin if it was added by notifications
                removeNotifyIndicator(fp);
                if (fp.classList.contains('pinned-by-notify')) {
                    fp.classList.remove('pinned-by-notify');
                    fp.classList.remove('pinned');
                }
                // If still pinned (by user), ensure the pin indicator is visible again
                if (fp.classList.contains('pinned')) {
                    ensurePinIndicator(fp);
                }
                const expanded = fp.querySelector('.model-options-expanded');
                if (expanded) {
                    const notifOption = expanded.querySelector('.option-icon[data-action="notifications"]');
                    if (notifOption) notifOption.classList.remove('active');
                    const pinOption = expanded.querySelector('.option-icon[data-action="pin"]');
                    if (pinOption) pinOption.classList.toggle('active', fp.classList.contains('pinned'));
                }
            }
            // Resort after any pin state changes
            resortNavModels();

            // Persist on backend via MainIn bridge
            try {
                const formElement = document.querySelector('.anvil-container');
                if (!formElement || typeof anvil === 'undefined' || !anvil.call) {
                    console.warn('⚠️ Cannot call MainIn_update_agent_notification: anvil or form element missing');
                } else {
                    const res = await anvil.call(formElement, 'MainIn_update_agent_notification', parseInt(modelId, 10), activating);
                    if (res !== 'success') throw new Error('Backend did not return success');
                }
            } catch (err) {
                console.error('❌ Error persisting notifications state, rolling back:', err);
                // Rollback UI to previous state
                fp.classList.toggle('notify-active', prevActive);
                fp.classList.toggle('pinned', prevPinned);
                if (prevPinnedByNotify) {
                    fp.classList.add('pinned-by-notify');
                } else {
                    fp.classList.remove('pinned-by-notify');
                }
                if (prevActive) {
                    ensureNotifyIndicator(fp);
                } else {
                    removeNotifyIndicator(fp);
                }
                if (prevPinned && !prevPinnedByNotify) {
                    ensurePinIndicator(fp);
                } else {
                    removePinIndicator(fp);
                }
                const expanded = fp.querySelector('.model-options-expanded');
                if (expanded) {
                    const notifOption = expanded.querySelector('.option-icon[data-action="notifications"]');
                    if (notifOption) notifOption.classList.toggle('active', prevActive);
                    const pinOption = expanded.querySelector('.option-icon[data-action="pin"]');
                    if (pinOption) pinOption.classList.toggle('active', prevPinned);
                }
                resortNavModels();
            }
            break;
        }
        case 'delete': {
            // Call into MainIn form method to handle confirm, delete, conditional navigation, and refresh
            try {
                const formElement = document.querySelector('.anvil-container');
                if (!formElement || typeof anvil === 'undefined' || !anvil.call) {
                    console.warn('⚠️ Cannot call MainIn_delete_model: anvil or form element missing');
                } else {
                    const ok = await anvil.call(formElement, 'MainIn_delete_model', parseInt(modelId, 10));
                    console.log('🗑️ Delete result:', ok);
                }
            } catch (err) {
                console.error('❌ Error during delete:', err);
            }
            break;
        }
    }

    // Close the menu after action
    closeAllMenus();
}

// 6. Close all open menus with improved cleanup
function closeAllMenus() {
    // Clear any active menu timeout
    if (window.activeMenuTimeout) {
        clearTimeout(window.activeMenuTimeout);
        window.activeMenuTimeout = null;
    }

    // Remove expanded class from all flow panels
    const expandedPanels = document.querySelectorAll('[anvil-role="nav_flow_panel"].expanded');
    expandedPanels.forEach(panel => {
        panel.classList.remove('expanded');

        // Remove expanded class from dots
        const dotsLink = panel.querySelector('[anvil-role="icon-link-discreet"]');
        if (dotsLink) {
            dotsLink.classList.remove('expanded');
        }

        // Remove expanded options
        const expandedContainer = panel.querySelector('.model-options-expanded');
        if (expandedContainer) {
            expandedContainer.classList.remove('active');
            setTimeout(() => {
                if (expandedContainer.parentNode) {
                    expandedContainer.remove();
                }
            }, 300);
        }
    });
}

// 7. Function to clear model navigation (for refresh)
function clearModelNavigation() {
    // Reset all state flags
    window.isMenuToggling = false;
    if (window.activeMenuTimeout) {
        clearTimeout(window.activeMenuTimeout);
        window.activeMenuTimeout = null;
    }
    closeAllMenus();

    // Remove JavaScript-added navigation items
    // These are <li> elements added by addNewModelToNavigation in DiscoverAgent.html
    const navModels = document.querySelector('.anvil-role-nav_models');
    if (navModels) {
        const linearPanel = navModels.querySelector('ul.linear-panel');
        if (linearPanel) {
            // Find all <li> elements that were added by JavaScript (not by Anvil)
            // Anvil-created items are wrapped in <li class="anvil-component">
            // JS-created items are just <li> without anvil-component class
            const jsAddedItems = Array.from(linearPanel.querySelectorAll('li:not(.anvil-component)'));
            jsAddedItems.forEach(item => {
                item.remove();
            });
        }
    }
}

// 8.1. Sync initial model states (pinned / notifications) after Anvil renders rows
function syncInitialModelStates(modelStates) {
    try {
        console.log('🧩 syncInitialModelStates called with:', modelStates);
        if (!Array.isArray(modelStates)) return;
        modelStates.forEach(state => {
            if (!state) return;
            const modelId = state.model_id != null ? String(state.model_id) : null;
            if (!modelId) return;
            const fp = findFlowPanelByModelId(modelId);
            if (!fp) return;

            const isPinned = !!state.is_pinned;
            const notifyActive = !!state.active_notifications;

            if (notifyActive) {
                fp.classList.add('notify-active');
                ensureNotifyIndicator(fp);
                removePinIndicator(fp);
                if (!fp.classList.contains('pinned')) {
                    fp.classList.add('pinned');
                    fp.classList.add('pinned-by-notify');
                }
            } else {
                fp.classList.remove('notify-active');
                removeNotifyIndicator(fp);
                fp.classList.remove('pinned-by-notify');
                if (isPinned) {
                    fp.classList.add('pinned');
                    ensurePinIndicator(fp);
                } else {
                    fp.classList.remove('pinned');
                    removePinIndicator(fp);
                }
            }
        });
    } catch (e) {
        console.warn('syncInitialModelStates error:', e);
    }
}

// Expose for Anvil call_js (global)
window.syncInitialModelStates = syncInitialModelStates;

// 8. Initialize when DOM is ready
console.log('🚀 Model navigation script loaded');
console.log('🚀 Document ready state:', document.readyState);

if (document.readyState === 'loading') {
    console.log('📅 Adding DOMContentLoaded listener');
    document.addEventListener('DOMContentLoaded', initializeModelNavigation);
} else {
    console.log('📅 DOM already ready, initializing immediately');
    initializeModelNavigation();
}

// Also try to initialize after a delay to catch Anvil's dynamic content
setTimeout(() => {
    console.log('⏰ Delayed initialization attempt');
    const existingDots = document.querySelectorAll('[anvil-role="icon-link-discreet"]');
    console.log('🔍 Found', existingDots.length, 'three-dot icons');
    existingDots.forEach((dot, index) => {
        console.log(`🔍 Dot ${index}:`, dot, 'Tag:', dot.getAttribute('tag'));
    });
}, 2000);
