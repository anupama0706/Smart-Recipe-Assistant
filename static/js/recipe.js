
/**
 * Smart Recipe Assistant - Recipe Studio Workflow
 * Full state orchestration and seamless single-page DOM transitions
 */

document.addEventListener('DOMContentLoaded', () => {
  // Application State
  const state = {
    mode: 'ingredients',
    dishes: [],
    selectedDish: '',
    servings: 2,
    availableIngredients: [],
    requiredIngredients: [],
    missingIngredients: [],
    finalIngredients: [],
    currentRecipe: null,
    activeSubstitutionTarget: null
  };

  // Section DOM elements
  const sectionDishes = document.getElementById('section-dishes');
  const sectionChecklist = document.getElementById('section-checklist');
  const sectionRecipeDisplay = document.getElementById('section-recipe-display');
  const dishesGrid = document.getElementById('dishes-grid');
  const dishesEmpty = document.getElementById('dishes-empty');

  // Nav Steps
  const stepNav1 = document.getElementById('step-nav-1');
  const stepNav2 = document.getElementById('step-nav-2');
  const stepNav3 = document.getElementById('step-nav-3');

  // Checklist DOM elements
  const checklistDishTitle = document.getElementById('checklist-dish-title');
  const checklistServingsVal = document.getElementById('checklist-servings-val');
  const checklistServingsDec = document.getElementById('checklist-servings-dec');
  const checklistServingsInc = document.getElementById('checklist-servings-inc');
  const availableList = document.getElementById('available-list');
  const missingList = document.getElementById('missing-list');
  const statTotalReq = document.getElementById('stat-total-req');
  const statAvailable = document.getElementById('stat-available');
  const statMissing = document.getElementById('stat-missing');
  const btnBackToDishes = document.getElementById('btn-back-to-dishes');
  const btnGenerateRecipe = document.getElementById('btn-generate-recipe');

  // Modal DOM elements
  const modalSub = document.getElementById('modal-substitution');
  const subTargetName = document.getElementById('sub-target-name');
  const subDishName = document.getElementById('sub-dish-name');
  const substitutesList = document.getElementById('substitutes-list');
  const subModalClose = document.getElementById('sub-modal-close');
  const subModalCancel = document.getElementById('sub-modal-cancel');

  // Recipe Display Elements
  const recipeDisplayTitle = document.getElementById('recipe-display-title');
  const recipePrepTime = document.getElementById('recipe-prep-time');
  const recipeCookTime = document.getElementById('recipe-cook-time');
  const recipeServingsVal = document.getElementById('recipe-servings-val');
  const recipeServingsDec = document.getElementById('recipe-servings-dec');
  const recipeServingsInc = document.getElementById('recipe-servings-inc');
  const recipeIngredientsChecklist = document.getElementById('recipe-ingredients-checklist');
  const recipeInstructionsList = document.getElementById('recipe-instructions-list');
  const btnSaveRecipe = document.getElementById('btn-save-recipe');
  const saveBtnText = document.getElementById('save-btn-text');
  const btnModifyIngredients = document.getElementById('btn-modify-ingredients');

  // Chat Elements
  const chatRecipeName = document.getElementById('chat-recipe-name');
  const chatGreetingDish = document.getElementById('chat-greeting-dish');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatQuickChips = document.getElementById('chat-quick-chips');

  // --------------------------------------------------------------------------
  // Navigation / Stepper Control
  // --------------------------------------------------------------------------
  function setStep(step) {
    [stepNav1, stepNav2, stepNav3].forEach((nav, idx) => {
      if (!nav) return;
      nav.classList.remove('active', 'completed');
      if (idx + 1 < step) {
        nav.classList.add('completed');
      } else if (idx + 1 === step) {
        nav.classList.add('active');
      }
    });

    sectionDishes.classList.add('hidden');
    sectionChecklist.classList.add('hidden');
    sectionRecipeDisplay.classList.add('hidden');

    if (step === 1) sectionDishes.classList.remove('hidden');
    if (step === 2) sectionChecklist.classList.remove('hidden');
    if (step === 3) sectionRecipeDisplay.classList.remove('hidden');

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // --------------------------------------------------------------------------
  // Initialize from Session Storage
  // --------------------------------------------------------------------------
  function init() {
    const rawData = sessionStorage.getItem('smart_recipe_data');
    if (!rawData) {
      if (dishesEmpty) dishesEmpty.classList.remove('hidden');
      return;
    }

    try {
      const parsed = JSON.parse(rawData);
      state.mode = parsed.mode || 'ingredients';
      state.servings = parsed.servings || 2;
      state.availableIngredients = parsed.availableIngredients || [];
      checklistServingsVal.textContent = state.servings;
      recipeServingsVal.textContent = state.servings;

      if (state.mode === 'dish' && parsed.selectedDish) {
        state.selectedDish = parsed.selectedDish;
        state.requiredIngredients = parsed.requiredIngredients || [];
        state.missingIngredients = parsed.missingIngredients || [];
        state.finalIngredients = [...state.requiredIngredients];
        renderChecklist();
        setStep(2);
      } else if (Array.isArray(parsed.dishes) && parsed.dishes.length > 0) {
        state.dishes = parsed.dishes;
        renderDishes(state.dishes);
        setStep(1);
      } else {
        if (dishesEmpty) dishesEmpty.classList.remove('hidden');
      }
    } catch (e) {
      if (dishesEmpty) dishesEmpty.classList.remove('hidden');
    }
  }

  // --------------------------------------------------------------------------
  // Step 1: Render Suggested Dishes
  // --------------------------------------------------------------------------
  function renderDishes(dishes) {
    if (!dishesGrid) return;
    dishesGrid.innerHTML = '';

    if (!dishes || dishes.length === 0) {
      if (dishesEmpty) dishesEmpty.classList.remove('hidden');
      return;
    }

    dishes.forEach((dish) => {
      const card = document.createElement('div');
      card.className = 'dish-card';

      const tags = (dish.available_ingredients_used || []).map(ing => 
        `<span class="tag-badge"><svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg> ${escapeHtml(ing)}</span>`
      ).join('');

      card.innerHTML = `
        <div class="dish-card-main">
          <div class="dish-card-top-row">
            <h3 class="dish-card-title">${escapeHtml(dish.name)}</h3>
          </div>
          <p class="dish-card-desc">${escapeHtml(dish.description)}</p>
          
          <div class="dish-card-pantry-row">
            <span class="dish-pantry-label">Uses from your pantry:</span>
            <div class="dish-ingredients-tags">
              ${tags || '<span class="text-muted">Basic pantry staples</span>'}
            </div>
          </div>
        </div>

        <div class="dish-card-action">
          <button type="button" class="btn btn-primary select-dish-btn" data-dish="${escapeHtml(dish.name)}">
            Open
          </button>
        </div>
      `;

      card.querySelector('.select-dish-btn').addEventListener('click', () => {
        selectDish(dish.name);
      });

      dishesGrid.appendChild(card);
    });
  }

  // --------------------------------------------------------------------------
  // Dish Selection Handler
  // --------------------------------------------------------------------------
  async function selectDish(dishName) {
    state.selectedDish = dishName;
    showLoader(`Analyzing required ingredients for "${dishName}"...`);

    try {
      // 1. Select dish endpoint
      await fetch('/api/select-dish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dish: dishName,
          available_ingredients: state.availableIngredients
        })
      });

      // 2. Generate Ingredients
      showLoader(`Generating ingredient proportions for ${state.servings} servings...`);
      const ingRes = await fetch('/api/generate-ingredients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dish: dishName,
          servings: state.servings
        })
      });
      const ingData = await ingRes.json();

      if (!ingRes.ok || !ingData.success) {
        hideLoader();
        showToast(ingData.error || 'Failed to generate ingredients.', 'error');
        return;
      }

      state.requiredIngredients = ingData.data.ingredients || [];
      state.finalIngredients = [...state.requiredIngredients];

      // 3. Check Missing Ingredients
      showLoader('Matching against your kitchen pantry...');
      const missRes = await fetch('/api/check-missing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          required_ingredients: state.requiredIngredients,
          available_ingredients: state.availableIngredients
        })
      });
      const missData = await missRes.json();
      hideLoader();

      if (missRes.ok && missData.success) {
        state.missingIngredients = missData.data.missing_ingredients || [];
      } else {
        state.missingIngredients = [];
      }

      renderChecklist();
      setStep(2);
    } catch (err) {
      hideLoader();
      showToast('Network error while analyzing dish ingredients.', 'error');
    }
  }

  // --------------------------------------------------------------------------
  // Step 2: Render Checklist (Available vs Missing)
  // --------------------------------------------------------------------------
  function renderChecklist() {
    checklistDishTitle.textContent = state.selectedDish;
    checklistServingsVal.textContent = state.servings;

    const reqList = state.finalIngredients.length > 0 ? state.finalIngredients : state.requiredIngredients;
    availableList.innerHTML = '';
    missingList.innerHTML = '';

    const missingSet = new Set(state.missingIngredients.map(m => m.toLowerCase()));
    let availableCount = 0;
    let missingCount = 0;

    reqList.forEach((item) => {
      const name = typeof item === 'object' ? item.name : item;
      const qty = typeof item === 'object' && item.quantity ? item.quantity : '';
      const category = typeof item === 'object' && item.category ? item.category : 'core';
      const isMissing = missingSet.has(name.toLowerCase());

      const li = document.createElement('li');
      li.className = `ingredient-item-card ${isMissing ? 'is-missing' : 'is-available'}`;

      if (isMissing) {
        missingCount++;
        li.innerHTML = `
          <div class="ingredient-item-details">
            <span class="ing-name">${escapeHtml(name)}</span>
            <span class="ing-qty">${escapeHtml(qty)} &bull; ${escapeHtml(category)}</span>
          </div>
          <button type="button" class="btn btn-outline btn-sm btn-find-sub" data-name="${escapeHtml(name)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.35rem;"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> Find Substitutes
          </button>
        `;

        li.querySelector('.btn-find-sub').addEventListener('click', () => {
          openSubstitutionModal(name);
        });
        missingList.appendChild(li);
      } else {
        availableCount++;
        li.innerHTML = `
          <div class="ingredient-item-details">
            <span class="ing-name">${escapeHtml(name)}</span>
            <span class="ing-qty">${escapeHtml(qty)} &bull; ${escapeHtml(category)}</span>
          </div>
          <span class="tag-badge">Ready in pantry</span>
        `;
        availableList.appendChild(li);
      }
    });

    if (missingCount === 0) {
      const emptyMsg = document.createElement('li');
      emptyMsg.className = 'ingredient-item-card is-available';
      emptyMsg.innerHTML = '<span class="ing-name"><svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" style="margin-right: 0.35rem; display: inline-block; vertical-align: -2px;"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg> You have all required ingredients!</span>';
      missingList.appendChild(emptyMsg);
    }

    statTotalReq.textContent = reqList.length;
    statAvailable.textContent = availableCount;
    statMissing.textContent = missingCount;
  }

  // Checklist Servings Adjustment
  if (checklistServingsDec && checklistServingsInc) {
    checklistServingsDec.addEventListener('click', () => changeChecklistServings(-1));
    checklistServingsInc.addEventListener('click', () => changeChecklistServings(1));
  }

  async function changeChecklistServings(delta) {
    const next = state.servings + delta;
    if (next < 1 || next > 20) return;
    state.servings = next;
    checklistServingsVal.textContent = state.servings;
    recipeServingsVal.textContent = state.servings;

    showLoader(`Recalculating portions for ${state.servings} servings...`);
    try {
      const res = await fetch('/api/generate-ingredients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dish: state.selectedDish,
          servings: state.servings
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        state.requiredIngredients = data.data.ingredients || [];
        state.finalIngredients = [...state.requiredIngredients];

        const missRes = await fetch('/api/check-missing', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            required_ingredients: state.requiredIngredients,
            available_ingredients: state.availableIngredients
          })
        });
        const missData = await missRes.json();
        if (missRes.ok && missData.success) {
          state.missingIngredients = missData.data.missing_ingredients || [];
        }
        renderChecklist();
      }
    } catch (e) {
      showToast('Could not scale servings.', 'error');
    } finally {
      hideLoader();
    }
  }

  if (btnBackToDishes) {
    btnBackToDishes.addEventListener('click', () => setStep(1));
  }
  // --------------------------------------------------------------------------
  // Step 3: Substitution Recommendation Modal
  // --------------------------------------------------------------------------
  async function openSubstitutionModal(missingIngredient) {
    state.activeSubstitutionTarget = missingIngredient;
    subTargetName.textContent = missingIngredient;
    subDishName.textContent = state.selectedDish;
    substitutesList.innerHTML = '';

    showLoader(`Chef AI is finding smart substitutes for "${missingIngredient}"...`);

    try {
      const res = await fetch('/api/substitutions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dish: state.selectedDish,
          missing_ingredient: missingIngredient,
          current_ingredients: state.finalIngredients
        })
      });
      const data = await res.json();
      hideLoader();

      if (!res.ok || !data.success) {
        showToast(data.error || 'No substitutes found.', 'error');
        return;
      }

      const substitutes = data.data.substitutes || [];
      if (substitutes.length === 0) {
        showToast('No direct culinary substitutes found.', 'info');
        return;
      }

      substitutes.forEach((sub) => {
        const card = document.createElement('div');
        card.className = 'substitute-card';
        card.innerHTML = `
          <div class="sub-header">
            <span class="sub-name">${escapeHtml(sub.name)}</span>
            <span class="sub-qty">${escapeHtml(sub.quantity)}</span>
          </div>
          <div class="sub-detail">
            <strong>Why it works:</strong> ${escapeHtml(sub.reason)}
          </div>
          <div class="sub-detail">
            <strong>Flavor &amp; texture impact:</strong> ${escapeHtml(sub.effect)}
          </div>
          <div class="sub-actions">
            <button type="button" class="btn btn-primary btn-sm btn-apply-sub">
              Apply This Substitute
            </button>
          </div>
        `;

        card.querySelector('.btn-apply-sub').addEventListener('click', () => {
          applySubstitution(missingIngredient, sub.name);
        });

        substitutesList.appendChild(card);
      });

      modalSub.classList.remove('hidden');
      modalSub.setAttribute('aria-hidden', 'false');
    } catch (err) {
      hideLoader();
      showToast('Error connecting to substitution service.', 'error');
    }
  }

  async function applySubstitution(missingName, substituteName) {
    showLoader(`Applying ${substituteName} to your recipe...`);
    try {
      const res = await fetch('/api/select-substitution', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          missing_ingredient: missingName,
          substitute: substituteName
        })
      });
      const data = await res.json();
      hideLoader();

      if (!res.ok || !data.success) {
        showToast(data.error || 'Failed to apply substitute.', 'error');
        return;
      }

      // Update final ingredients list in local state
      state.finalIngredients = data.data.final_ingredients || state.finalIngredients;

      // Remove from missing list
      state.missingIngredients = state.missingIngredients.filter(
        item => item.toLowerCase() !== missingName.toLowerCase()
      );

      closeSubModal();
      renderChecklist();
      showToast(`Substituted "${missingName}" with "${substituteName}"!`, 'success');
    } catch (err) {
      hideLoader();
      showToast('Error applying substitution.', 'error');
    }
  }

  function closeSubModal() {
    modalSub.classList.add('hidden');
    modalSub.setAttribute('aria-hidden', 'true');
    state.activeSubstitutionTarget = null;
  }

  if (subModalClose) subModalClose.addEventListener('click', closeSubModal);
  if (subModalCancel) subModalCancel.addEventListener('click', closeSubModal);
  modalSub.addEventListener('click', (e) => {
    if (e.target === modalSub) closeSubModal();
  });

  // --------------------------------------------------------------------------
  // Step 4: Final Recipe Generation & Display
  // --------------------------------------------------------------------------
  if (btnGenerateRecipe) {
    btnGenerateRecipe.addEventListener('click', async () => {
      showLoader(`Chef AI is creating your complete step-by-step recipe...`);

      try {
        const res = await fetch('/api/generate-recipe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dish: state.selectedDish,
            servings: state.servings,
            ingredients: state.finalIngredients
          })
        });
        const data = await res.json();
        hideLoader();

        if (!res.ok || !data.success) {
          showToast(data.error || 'Failed to generate recipe.', 'error');
          return;
        }

        state.currentRecipe = data.data;
        renderFinalRecipe(state.currentRecipe);
        setStep(3);
        showToast('Recipe ready! Happy cooking.', 'success');
      } catch (err) {
        hideLoader();
        showToast('Network error while generating final recipe.', 'error');
      }
    });
  }

  function renderFinalRecipe(recipe) {
    recipeDisplayTitle.textContent = recipe.dish_name;
    recipePrepTime.textContent = recipe.preparation_time || '15 mins';
    recipeCookTime.textContent = recipe.cook_time || '25 mins';
    recipeServingsVal.textContent = recipe.servings || state.servings;

    // Reset save button state
    saveBtnText.textContent = 'Save Recipe';
    btnSaveRecipe.classList.remove('btn-success');
    btnSaveRecipe.disabled = false;

    // Render interactive checklist
    recipeIngredientsChecklist.innerHTML = '';
    const ingredients = recipe.ingredients || [];
    ingredients.forEach((ing) => {
      const name = typeof ing === 'object' ? ing.name : ing;
      const qty = typeof ing === 'object' && ing.quantity ? ing.quantity : '';

      const li = document.createElement('li');
      li.className = 'recipe-ing-check-item';
      li.innerHTML = `
        <input type="checkbox" class="recipe-checkbox" aria-label="Cross off ${escapeHtml(name)}">
        <label><strong>${escapeHtml(qty)}</strong> ${escapeHtml(name)}</label>
      `;

      li.addEventListener('click', (e) => {
        const checkbox = li.querySelector('.recipe-checkbox');
        if (e.target !== checkbox) {
          checkbox.checked = !checkbox.checked;
        }
        li.classList.toggle('checked', checkbox.checked);
      });

      recipeIngredientsChecklist.appendChild(li);
    });

    // Render numbered instructions
    recipeInstructionsList.innerHTML = '';
    const instructions = recipe.instructions || [];
    instructions.forEach((stepText) => {
      const li = document.createElement('li');
      li.className = 'instruction-step';
      const cleanText = (typeof stepText === 'string' ? stepText : String(stepText || '')).replace(/^\d+[\.\)]\s*/, '');
      li.textContent = cleanText;
      recipeInstructionsList.appendChild(li);
    });

    // Update Chef AI Chat context
    chatRecipeName.textContent = recipe.dish_name;
    chatGreetingDish.textContent = recipe.dish_name;

    // Trigger nutrition analysis
    const ings = recipe.ingredients || state.finalIngredients || [];
    const sVal = recipe.servings || state.servings || 2;
    if (ings.length > 0) {
      loadNutritionData(ings, sVal);
    }
  }

  // --------------------------------------------------------------------------
  // Nutrition Breakdown Calculation & Display
  // --------------------------------------------------------------------------
  function estimateNutrients(name) {
    const lower = (name || '').toLowerCase();
    const db = {
      chicken: { calories: 240, protein: 31, carbohydrates: 0, fat: 3.6, fiber: 0, sugar: 0 },
      egg: { calories: 72, protein: 6.3, carbohydrates: 0.4, fat: 4.8, fiber: 0, sugar: 0.2 },
      rice: { calories: 206, protein: 4.3, carbohydrates: 45, fat: 0.4, fiber: 0.6, sugar: 0.1 },
      pasta: { calories: 220, protein: 8, carbohydrates: 43, fat: 1.3, fiber: 2.5, sugar: 0.8 },
      tomato: { calories: 22, protein: 1.1, carbohydrates: 4.8, fat: 0.2, fiber: 1.5, sugar: 3.2 },
      potato: { calories: 161, protein: 4.3, carbohydrates: 37, fat: 0.2, fiber: 3.8, sugar: 1.7 },
      onion: { calories: 44, protein: 1.2, carbohydrates: 10, fat: 0.1, fiber: 1.9, sugar: 4.7 },
      garlic: { calories: 15, protein: 0.6, carbohydrates: 3.3, fat: 0.1, fiber: 0.2, sugar: 0.1 },
      broccoli: { calories: 55, protein: 3.7, carbohydrates: 11, fat: 0.6, fiber: 5.1, sugar: 2.6 },
      capsicum: { calories: 30, protein: 1.0, carbohydrates: 6.0, fat: 0.2, fiber: 2.1, sugar: 4.2 },
      cheese: { calories: 113, protein: 7, carbohydrates: 0.4, fat: 9.3, fiber: 0, sugar: 0.1 },
      milk: { calories: 122, protein: 8, carbohydrates: 12, fat: 4.8, fiber: 0, sugar: 12 },
      spinach: { calories: 23, protein: 2.9, carbohydrates: 3.6, fat: 0.4, fiber: 2.2, sugar: 0.4 },
      bean: { calories: 127, protein: 8.7, carbohydrates: 22.8, fat: 0.5, fiber: 7.4, sugar: 0.6 },
      oil: { calories: 120, protein: 0, carbohydrates: 0, fat: 14, fiber: 0, sugar: 0 },
      butter: { calories: 102, protein: 0.1, carbohydrates: 0, fat: 11.5, fiber: 0, sugar: 0 },
    };

    for (const [key, val] of Object.entries(db)) {
      if (lower.includes(key)) {
        return { ...val };
      }
    }
    return { calories: 50, protein: 2, carbohydrates: 8, fat: 1, fiber: 1, sugar: 1 };
  }

  async function loadNutritionData(ingredients, servings) {
    if (!ingredients || !ingredients.length) return;

    const parsedServings = parseInt(servings, 10) || state.servings || 2;
    const nutritionLoading = document.getElementById('nutrition-loading');

    if (nutritionLoading) nutritionLoading.style.display = 'block';

    const payloadIngredients = ingredients.map((item) => {
      if (typeof item === 'object' && item !== null) {
        return {
          name: item.name || 'Ingredient',
          nutrition: item.nutrition || estimateNutrients(item.name || ''),
        };
      }
      return {
        name: String(item),
        nutrition: estimateNutrients(String(item)),
      };
    });

    try {
      const response = await fetch('/api/nutrition/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ingredients: payloadIngredients,
          servings: parseInt(parsedServings, 10),
        }),
      });

      const json = await response.json();
      if (response.ok && json.success && json.data) {
        const total = json.data.total_nutrition || {};
        const perServing = json.data.per_serving || {};

        const setCell = (id, val, unit = '') => {
          const el = document.getElementById(id);
          if (el) el.textContent = val !== undefined && val !== null ? `${val}${unit ? ' ' + unit : ''}` : '—';
        };

        setCell('nutrition-total-calories', total.calories);
        setCell('nutrition-serving-calories', perServing.calories);

        setCell('nutrition-total-protein', total.protein, 'g');
        setCell('nutrition-serving-protein', perServing.protein, 'g');

        setCell('nutrition-total-carbohydrates', total.carbohydrates, 'g');
        setCell('nutrition-serving-carbohydrates', perServing.carbohydrates, 'g');

        setCell('nutrition-total-fat', total.fat, 'g');
        setCell('nutrition-serving-fat', perServing.fat, 'g');

        setCell('nutrition-total-fiber', total.fiber, 'g');
        setCell('nutrition-serving-fiber', perServing.fiber, 'g');

        setCell('nutrition-total-sugar', total.sugar, 'g');
        setCell('nutrition-serving-sugar', perServing.sugar, 'g');

        // Update static serving indicators
        const badgeCount = document.getElementById('nutrition-servings-count');
        if (badgeCount) badgeCount.textContent = parsedServings;
        const colServings = document.getElementById('nutrition-col-servings');
        if (colServings) colServings.textContent = parsedServings;
      } else {
        console.warn('Failed to calculate nutrition data:', json.error);
      }
    } catch (err) {
      console.error('Network error during nutrition analysis:', err);
    } finally {
      if (nutritionLoading) nutritionLoading.style.display = 'none';
    }
  }

  window.loadNutritionData = loadNutritionData;

  // Stepper within recipe view
  if (recipeServingsDec && recipeServingsInc) {
    recipeServingsDec.addEventListener('click', () => {
      if (state.servings > 1) {
        state.servings--;
        recipeServingsVal.textContent = state.servings;
        showToast(`Portion adjusted to ${state.servings} servings. Scale ingredients accordingly!`, 'info');
        if (typeof loadNutritionData === 'function') {
          const ings = (state.currentRecipe && state.currentRecipe.ingredients) || state.finalIngredients || [];
          if (ings.length > 0) {
            loadNutritionData(ings, state.servings);
          }
        }
      }
    });

    recipeServingsInc.addEventListener('click', () => {
      if (state.servings < 20) {
        state.servings++;
        recipeServingsVal.textContent = state.servings;
        showToast(`Portion adjusted to ${state.servings} servings. Scale ingredients accordingly!`, 'info');
        if (typeof loadNutritionData === 'function') {
          const ings = (state.currentRecipe && state.currentRecipe.ingredients) || state.finalIngredients || [];
          if (ings.length > 0) {
            loadNutritionData(ings, state.servings);
          }
        }
      }
    });
  }

  if (btnModifyIngredients) {
    btnModifyIngredients.addEventListener('click', () => setStep(2));
  }

  // --------------------------------------------------------------------------
  // Step 5: Save Recipe to Cookbook
  // --------------------------------------------------------------------------
  if (btnSaveRecipe) {
    btnSaveRecipe.addEventListener('click', async () => {
      if (!state.currentRecipe) {
        showToast('Generate a recipe first before saving.', 'warning');
        return;
      }

      showLoader('Saving recipe to your personal cookbook...');
      try {
        const res = await fetch('/api/recipes/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        hideLoader();

        if (res.status === 401) {
          showToast('Please log in to save recipes to your cookbook.', 'warning');
          return;
        }

        if (res.ok && data.success) {
          saveBtnText.textContent = 'Saved to Cookbook!';
          btnSaveRecipe.classList.add('btn-success');
          btnSaveRecipe.disabled = true;
          showToast(`"${state.currentRecipe.dish_name}" saved to your cookbook!`, 'success');
        } else {
          showToast(data.error || 'Could not save recipe.', 'error');
        }
      } catch (err) {
        hideLoader();
        showToast('Error saving recipe.', 'error');
      }
    });
  }

  // --------------------------------------------------------------------------
  // Step 6: Interactive Recipe-Aware Chat
  // --------------------------------------------------------------------------
  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const message = chatInput.value.trim();
      if (!message) return;
      chatInput.value = '';
      sendChefChatMessage(message);
    });
  }

  // Quick Prompt Chips
  if (chatQuickChips) {
    chatQuickChips.addEventListener('click', (e) => {
      const chip = e.target.closest('.quick-chip');
      if (!chip) return;
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        sendChefChatMessage(prompt);
      }
    });
  }

  async function sendChefChatMessage(messageText) {
    // Append user message bubble
    appendChatBubble('user', messageText);

    // Append typing indicator bubble
    const typingBubble = document.createElement('div');
    typingBubble.className = 'chat-bubble chat-bubble-ai typing-indicator-bubble';
    typingBubble.innerHTML = `
      <div class="bubble-avatar">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 13.8a4 4 0 0 1 0-7.6 4 4 0 0 1 7.2-2.3 4 4 0 0 1 4.8 4.3A4 4 0 0 1 18 13.8"></path>
          <path d="M6 17h12"></path>
          <path d="M6 21h12"></path>
        </svg>
      </div>
      <div class="bubble-content">
        <div class="typing-dots">
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
          <span class="typing-dot"></span>
        </div>
      </div>
    `;
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      });
      const data = await res.json();
      typingBubble.remove();

      if (res.ok && data.success && data.data) {
        appendChatBubble('ai', data.data.answer);
      } else {
        appendChatBubble('ai', data.error || 'Sorry, I could not process your question right now.');
      }
    } catch (err) {
      typingBubble.remove();
      appendChatBubble('ai', 'Connection error. Please try asking again.');
    }
  }

  function appendChatBubble(sender, text) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble chat-bubble-${sender}`;
    const avatar = sender === 'user' 
      ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
      : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 13.8a4 4 0 0 1 0-7.6 4 4 0 0 1 7.2-2.3 4 4 0 0 1 4.8 4.3A4 4 0 0 1 18 13.8"></path><path d="M6 17h12"></path><path d="M6 21h12"></path></svg>';

    bubble.innerHTML = `
      <div class="bubble-avatar">${avatar}</div>
      <div class="bubble-content">
        <p>${escapeHtml(text)}</p>
      </div>
    `;

    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Helper: Sanitize HTML
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/[&<>"']/g, (m) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
  }

  // Initialize workflow
  init();
});
