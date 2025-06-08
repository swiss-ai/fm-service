// Global variables
let elosData = {};
let detailsData = [];
let displayedComparisons = [];
let currentPage = 0;
const PAGE_SIZE = 100;
let selectedModel1 = '';
let selectedModel2 = '';

// Initialize the application
async function init() {
    try {
        // Fetch data from JSON files
        const [elosResponse, detailsResponse] = await Promise.all([
            fetch('elos.json'),
            fetch('details.json')
        ]);
        
        elosData = await elosResponse.json();
        detailsData = await detailsResponse.json();
        
        // Populate model dropdowns
        populateModelDropdowns();
        
        // Render initial views
        renderRankings();
        filterComparisons();
        
        // Set up event listeners
        setupEventListeners();
    } catch (error) {
        console.error('Failed to load JSON data:', error);
        document.body.innerHTML = `
            <div class="container py-5 text-center">
                <div class="alert alert-danger">
                    <h4>Error Loading Data</h4>
                    <p>Could not load the JSON files. Make sure elos.json and details.json are available.</p>
                    <p class="text-muted">Technical details: ${error.message}</p>
                </div>
            </div>
        `;
    }
}

// Set up event listeners
function setupEventListeners() {
    // Toggle between ranking and details pages
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const pageName = btn.dataset.page;
            
            // Update active button
            document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show the selected page
            if (pageName === 'ranking') {
                document.getElementById('ranking-page').classList.remove('d-none');
                document.getElementById('details-page').classList.add('d-none');
            } else {
                document.getElementById('ranking-page').classList.add('d-none');
                document.getElementById('details-page').classList.remove('d-none');
            }
        });
    });
    
    // Model selection events
    document.getElementById('model1-select').addEventListener('change', function() {
        selectedModel1 = this.value;
        const model2Select = document.getElementById('model2-select');
        
        if (selectedModel1) {
            model2Select.disabled = false;
            populateModel2Dropdown();
        } else {
            model2Select.disabled = true;
            model2Select.innerHTML = '<option value="">Select Model 2</option>';
            selectedModel2 = '';
        }
        
        currentPage = 0;
        filterComparisons();
    });
    
    document.getElementById('model2-select').addEventListener('change', function() {
        selectedModel2 = this.value;
        currentPage = 0;
        filterComparisons();
    });
    
    document.getElementById('reset-filters').addEventListener('click', function() {
        selectedModel1 = '';
        selectedModel2 = '';
        document.getElementById('model1-select').value = '';
        
        const model2Select = document.getElementById('model2-select');
        model2Select.value = '';
        model2Select.disabled = true;
        
        currentPage = 0;
        filterComparisons();
    });
    
    document.getElementById('load-more').addEventListener('click', function() {
        currentPage++;
        appendComparisons();
    });
    
    // Add global event listener for expandable content
    document.addEventListener('click', function(e) {
        // Check if clicked element has expandable parent
        if (e.target.closest('.expand-btn')) {
            const expandable = e.target.closest('.expandable');
            expandable.classList.add('expanded');
        }
        
        if (e.target.closest('.collapse-btn')) {
            const collapseBtn = e.target.closest('.collapse-btn');
            const expandable = document.getElementById(collapseBtn.dataset.target);
            expandable.classList.remove('expanded');
        }
    });
}

// Populate model dropdowns
function populateModelDropdowns() {
    // Get unique models from the new data structure
    const uniqueModels = new Set();
    
    // Add models from elos data
    Object.keys(elosData).forEach(model => {
        uniqueModels.add(model);
    });
    
    // Add models from details data
    detailsData.forEach(comp => {
        uniqueModels.add(comp.model1);
        uniqueModels.add(comp.model2);
    });
    
    const model1Select = document.getElementById('model1-select');
    
    // Clear existing options except the first one
    model1Select.innerHTML = '<option value="">Select Model 1</option>';
    
    // Add model options
    Array.from(uniqueModels).sort().forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        model1Select.appendChild(option);
    });
}

// Populate model2 dropdown based on model1 selection
function populateModel2Dropdown() {
    // Get unique models that have comparisons with model1
    const uniqueModels = new Set();
    
    detailsData.forEach(comp => {
        if (comp.model1 === selectedModel1) {
            uniqueModels.add(comp.model2);
        } else if (comp.model2 === selectedModel1) {
            uniqueModels.add(comp.model1);
        }
    });
    
    const model2Select = document.getElementById('model2-select');
    
    // Clear existing options except the first one
    model2Select.innerHTML = '<option value="">Select Model 2</option>';
    
    // Add model options
    Array.from(uniqueModels).sort().forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        model2Select.appendChild(option);
    });
}

// Render rankings table
function renderRankings() {
    const tableBody = document.getElementById('ranking-body');
    tableBody.innerHTML = '';
    
    // Convert object to array of [model, rating] pairs and sort by rating (descending)
    const sortedModels = Object.entries(elosData).sort((a, b) => b[1] - a[1]);
    
    sortedModels.forEach((model, index) => {
        const row = document.createElement('tr');
        
        const rankCell = document.createElement('td');
        rankCell.textContent = index + 1;
        
        const modelCell = document.createElement('td');
        modelCell.textContent = model[0];
        
        const eloCell = document.createElement('td');
        eloCell.textContent = Math.round(model[1]); // Round to nearest integer for cleaner display
        
        row.appendChild(rankCell);
        row.appendChild(modelCell);
        row.appendChild(eloCell);
        
        tableBody.appendChild(row);
    });
}

// Filter comparisons based on selected models
function filterComparisons() {
    const container = document.getElementById('comparisons-container');
    container.innerHTML = '';
    
    // Filter comparisons based on selected models
    if (!selectedModel1) {
        // Show all comparisons
        displayedComparisons = [...detailsData];
    } else if (selectedModel1 && !selectedModel2) {
        // Show comparisons involving model1
        displayedComparisons = detailsData.filter(comp => 
            comp.model1 === selectedModel1 || comp.model2 === selectedModel1
        );
    } else {
        // Show comparisons between model1 and model2
        displayedComparisons = detailsData.filter(comp => 
            (comp.model1 === selectedModel1 && comp.model2 === selectedModel2) ||
            (comp.model1 === selectedModel2 && comp.model2 === selectedModel1)
        );
    }
    
    appendComparisons();
}

// Create an expandable content element
function createExpandableContent(content, id, type = 'text') {
    const expandableId = `expandable-${id}-${type}`;
    
    const container = document.createElement('div');
    container.className = 'expandable-container';
    
    const expandable = document.createElement('div');
    expandable.className = 'expandable';
    expandable.id = expandableId;
    
    if (type === 'text') {
        // For text content, add each paragraph in its own div for better control
        const lines = content.split('\n');
        const formattedContent = lines.map(line => {
            if (line.trim().length === 0) return '<div class="py-1"></div>'; // Empty line spacer
            return `<div>${line}</div>`;
        }).join('');
        expandable.innerHTML = formattedContent;
    } else {
        expandable.innerHTML = content;
    }
    
    const expandBtn = document.createElement('div');
    expandBtn.className = 'expand-btn';
    expandBtn.innerHTML = '<span class="badge bg-light text-dark">Show more</span>';
    expandable.appendChild(expandBtn);
    
    container.appendChild(expandable);
    
    const collapseBtn = document.createElement('div');
    collapseBtn.className = 'collapse-btn';
    collapseBtn.dataset.target = expandableId;
    collapseBtn.innerHTML = '<span class="badge bg-light text-dark">Show less</span>';
    container.appendChild(collapseBtn);
    
    return container;
}

// Append comparisons to the container
function appendComparisons() {
    const container = document.getElementById('comparisons-container');
    const startIndex = currentPage * PAGE_SIZE;
    const endIndex = startIndex + PAGE_SIZE;
    const compareData = displayedComparisons.slice(startIndex, endIndex);
    
    if (compareData.length === 0 && currentPage === 0) {
        container.innerHTML = '<div class="alert alert-info">No comparisons found for the selected criteria.</div>';
        document.getElementById('load-more').style.display = 'none';
        return;
    }
    
    compareData.forEach((comp, index) => {
        const card = document.createElement('div');
        card.className = 'card shadow-sm mb-4';
        
        // Main content of the card
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Question/Prompt - 100% width expandable
        const promptContainer = document.createElement('div');
        promptContainer.className = 'mb-3';
        
        const promptHeader = document.createElement('h5');
        promptHeader.className = 'mb-2';
        promptHeader.textContent = `Question #${comp.response_idx}`;
        promptContainer.appendChild(promptHeader);
        
        const promptContent = createExpandableContent(comp.prompt, `${comp.response_idx}-${index}-prompt`);
        promptContainer.appendChild(promptContent);
        
        cardBody.appendChild(promptContainer);
        
        // Responses section - two 50% width columns
        const responsesRow = document.createElement('div');
        responsesRow.className = 'row mb-3';
        
        // Determine outcome for each response
        const model1Winner = comp.winner === comp.model1;
        const model2Winner = comp.winner === comp.model2;
        const isDraw = comp.winner === 'draw' || (!comp.winner && !comp.loser);
        
        // Model 1 Response - 50% width
        const response1Col = document.createElement('div');
        response1Col.className = 'col-md-6 mb-3 mb-md-0';
        
        const response1Element = document.createElement('div');
        response1Element.className = 'model-response';
        
        if (isDraw) {
            response1Element.classList.add('draw-response');
        } else if (model1Winner) {
            response1Element.classList.add('winner-response');
        } else {
            response1Element.classList.add('loser-response');
        }
        
        const model1Header = document.createElement('h6');
        model1Header.className = 'mb-2';
        model1Header.textContent = comp.model1;
        response1Element.appendChild(model1Header);
        
        const response1Content = createExpandableContent(comp.response1, `${comp.response_idx}-${index}-resp1`);
        response1Element.appendChild(response1Content);
        
        response1Col.appendChild(response1Element);
        responsesRow.appendChild(response1Col);
        
        // Model 2 Response - 50% width
        const response2Col = document.createElement('div');
        response2Col.className = 'col-md-6';
        
        const response2Element = document.createElement('div');
        response2Element.className = 'model-response';
        
        if (isDraw) {
            response2Element.classList.add('draw-response');
        } else if (model2Winner) {
            response2Element.classList.add('winner-response');
        } else {
            response2Element.classList.add('loser-response');
        }
        
        const model2Header = document.createElement('h6');
        model2Header.className = 'mb-2';
        model2Header.textContent = comp.model2;
        response2Element.appendChild(model2Header);
        
        const response2Content = createExpandableContent(comp.response2, `${comp.response_idx}-${index}-resp2`);
        response2Element.appendChild(response2Content);
        
        response2Col.appendChild(response2Element);
        responsesRow.appendChild(response2Col);
        
        cardBody.appendChild(responsesRow);
        
        // Reasoning section - 100% width
        if (comp.votes && Object.keys(comp.votes).length > 0) {
            const reasoningContainer = document.createElement('div');
            reasoningContainer.className = 'mt-3';
            
            const reasoningTitle = document.createElement('h6');
            reasoningTitle.className = 'mb-2';
            reasoningTitle.textContent = 'Voter Reasonings';
            reasoningContainer.appendChild(reasoningTitle);
            
            // Create reasoning content
            let reasoningHTML = '';
            Object.entries(comp.votes).forEach(([voter, decision]) => {
                reasoningHTML += `<div class="mb-2"><strong>${voter}:</strong> `;
                if (decision.reasoning) {
                    reasoningHTML += `${decision.reasoning}`;
                } else if (decision.winner === 'draw') {
                    reasoningHTML += 'Draw - both responses are considered equal.';
                } else {
                    reasoningHTML += `Winner: ${decision.winner}`;
                }
                reasoningHTML += '</div>';
            });
            
            const reasoningContent = createExpandableContent(reasoningHTML, `${comp.response_idx}-${index}-reasoning`, 'html');
            reasoningContainer.appendChild(reasoningContent);
            
            cardBody.appendChild(reasoningContainer);
        }
        
        card.appendChild(cardBody);
        container.appendChild(card);
    });
    
    // Show/hide load more button
    const loadMoreButton = document.getElementById('load-more');
    if (endIndex >= displayedComparisons.length) {
        loadMoreButton.style.display = 'none';
    } else {
        loadMoreButton.style.display = 'block';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', init);
