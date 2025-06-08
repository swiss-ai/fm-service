<script>
  import { getModelLogo } from '@lib/modelLogos';
  
  export let elosData = {};
  export let detailsData = [];

  let models = [];
  let selectedModel1 = '';
  let selectedModel2 = '';
  let filteredComparisons = [];
  let displayedComparisons = [];
  let currentPage = 0;
  const PAGE_SIZE = 10;

  $: {
    if (elosData && detailsData) {
      // Get unique models
      const uniqueModels = new Set();
      Object.keys(elosData).forEach(model => uniqueModels.add(model));
      detailsData.forEach(comp => {
        uniqueModels.add(comp.model1);
        uniqueModels.add(comp.model2);
      });
      models = Array.from(uniqueModels).sort();
      
      // Filter comparisons
      filterComparisons();
    }
  }

  $: model2Options = getModel2Options();

  function getDisplayName(modelName) {
    return modelName.replace('-responses', '').replace(/apertus3-/, '');
  }

  function getModel2Options() {
    if (!selectedModel1 || !detailsData.length) return [];
    
    const uniqueModels = new Set();
    detailsData.forEach(comp => {
      if (comp.model1 === selectedModel1) {
        uniqueModels.add(comp.model2);
      } else if (comp.model2 === selectedModel1) {
        uniqueModels.add(comp.model1);
      }
    });
    
    return Array.from(uniqueModels).sort();
  }

  function filterComparisons() {
    if (!selectedModel1) {
      filteredComparisons = [...detailsData];
    } else if (selectedModel1 && !selectedModel2) {
      filteredComparisons = detailsData.filter(comp => 
        comp.model1 === selectedModel1 || comp.model2 === selectedModel1
      );
    } else {
      filteredComparisons = detailsData.filter(comp => 
        (comp.model1 === selectedModel1 && comp.model2 === selectedModel2) ||
        (comp.model1 === selectedModel2 && comp.model2 === selectedModel1)
      );
    }
    
    currentPage = 0;
    updateDisplayedComparisons();
  }

  function updateDisplayedComparisons() {
    const startIndex = 0;
    const endIndex = (currentPage + 1) * PAGE_SIZE;
    displayedComparisons = filteredComparisons.slice(startIndex, endIndex);
  }

  function loadMore() {
    currentPage++;
    updateDisplayedComparisons();
  }

  function resetFilters() {
    selectedModel1 = '';
    selectedModel2 = '';
    currentPage = 0;
    filterComparisons();
  }

  function getWinnerInfo(comp) {
    const model1Winner = comp.winner === comp.model1;
    const model2Winner = comp.winner === comp.model2;
    const isDraw = comp.winner === 'draw' || (!comp.winner && !comp.loser);
    
    return {
      model1Winner,
      model2Winner,
      isDraw,
      winnerText: isDraw ? 'Draw' : comp.winner
    };
  }

  function formatVotes(votes) {
    if (!votes || Object.keys(votes).length === 0) return '';
    
    return Object.entries(votes).map(([voter, decision]) => {
      const reasoning = decision.reasoning || 
        (decision.winner === 'draw' ? 'Draw - both responses are considered equal.' : `Winner: ${decision.winner}`);
      return `${voter}: ${reasoning}`;
    }).join('\n\n');
  }

  function truncateText(text, maxLength = 200) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }

  let expandedItems = new Set();

  function toggleExpanded(id) {
    if (expandedItems.has(id)) {
      expandedItems.delete(id);
    } else {
      expandedItems.add(id);
    }
    expandedItems = expandedItems; // Trigger reactivity
  }
</script>

<div class="space-y-6">
  <!-- Filters -->
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Filter Comparisons</h3>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label for="model1-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Model 1
        </label>
        <select 
          id="model1-select"
          bind:value={selectedModel1}
          on:change={filterComparisons}
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
        >
          <option value="">Select Model 1</option>
          {#each models as model}
            <option value={model}>{getDisplayName(model)}</option>
          {/each}
        </select>
      </div>

      <div>
        <label for="model2-select" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Model 2
        </label>
        <select 
          id="model2-select"
          bind:value={selectedModel2}
          on:change={filterComparisons}
          disabled={!selectedModel1}
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <option value="">Select Model 2</option>
          {#each model2Options as model}
            <option value={model}>{getDisplayName(model)}</option>
          {/each}
        </select>
      </div>

      <div class="flex items-end">
        <button 
          on:click={resetFilters}
          class="w-full px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white font-medium rounded-md transition-colors"
        >
          Reset Filters
        </button>
      </div>
    </div>

    <div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
      Showing {Math.min(displayedComparisons.length, filteredComparisons.length)} of {filteredComparisons.length} comparisons
    </div>
  </div>

  <!-- Comparisons -->
  {#if filteredComparisons.length === 0}
    <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
      <p class="text-blue-800 dark:text-blue-200">No comparisons found for the selected criteria.</p>
    </div>
  {:else}
    <div class="space-y-6">
      {#each displayedComparisons as comp, index}
        {@const winnerInfo = getWinnerInfo(comp)}
        {@const compId = `${comp.response_idx}-${index}`}
        {@const isExpanded = expandedItems.has(compId)}
        
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <!-- Header -->
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <div class="flex items-center justify-between">
              <h4 class="text-lg font-semibold text-gray-900 dark:text-white">
                Question #{comp.response_idx}
              </h4>
              <div class="flex items-center space-x-2">
                {#if winnerInfo.isDraw}
                  <span class="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200 text-sm font-medium rounded-full">
                    Draw
                  </span>
                {:else}
                  <span class="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 text-sm font-medium rounded-full">
                    Winner: {getDisplayName(comp.winner)}
                  </span>
                {/if}
              </div>
            </div>
          </div>

          <!-- Prompt -->
          <div class="p-6 border-b border-gray-200 dark:border-gray-700">
            <h5 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Prompt</h5>
            <div class="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
              {#if isExpanded || comp.prompt.length <= 200}
                {comp.prompt}
              {:else}
                {truncateText(comp.prompt)}
                <button 
                  on:click={() => toggleExpanded(`${compId}-prompt`)}
                  class="ml-2 text-blue-600 dark:text-blue-400 hover:underline text-sm"
                >
                  Show more
                </button>
              {/if}
            </div>
          </div>

          <!-- Responses -->
          <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-200 dark:divide-gray-700">
            <!-- Model 1 Response -->
            <div class="p-6 {winnerInfo.model1Winner ? 'bg-green-50 dark:bg-green-900/10' : winnerInfo.isDraw ? 'bg-gray-50 dark:bg-gray-800/50' : 'bg-red-50 dark:bg-red-900/10'}">
              <div class="flex items-center space-x-3 mb-3">
                {#if getModelLogo(comp.model1)}
                  <img src={getModelLogo(comp.model1)} alt="" class="w-6 h-6 rounded" />
                {/if}
                <h6 class="font-semibold text-gray-900 dark:text-white">
                  {getDisplayName(comp.model1)}
                </h6>
                {#if winnerInfo.model1Winner}
                  <span class="text-green-600 dark:text-green-400 text-lg">🏆</span>
                {/if}
              </div>
              <div class="text-gray-900 dark:text-gray-100 text-sm whitespace-pre-wrap">
                {#if isExpanded || comp.response1.length <= 200}
                  {comp.response1}
                {:else}
                  {truncateText(comp.response1)}
                  <button 
                    on:click={() => toggleExpanded(`${compId}-resp1`)}
                    class="ml-2 text-blue-600 dark:text-blue-400 hover:underline text-sm"
                  >
                    Show more
                  </button>
                {/if}
              </div>
            </div>

            <!-- Model 2 Response -->
            <div class="p-6 {winnerInfo.model2Winner ? 'bg-green-50 dark:bg-green-900/10' : winnerInfo.isDraw ? 'bg-gray-50 dark:bg-gray-800/50' : 'bg-red-50 dark:bg-red-900/10'}">
              <div class="flex items-center space-x-3 mb-3">
                {#if getModelLogo(comp.model2)}
                  <img src={getModelLogo(comp.model2)} alt="" class="w-6 h-6 rounded" />
                {/if}
                <h6 class="font-semibold text-gray-900 dark:text-white">
                  {getDisplayName(comp.model2)}
                </h6>
                {#if winnerInfo.model2Winner}
                  <span class="text-green-600 dark:text-green-400 text-lg">🏆</span>
                {/if}
              </div>
              <div class="text-gray-900 dark:text-gray-100 text-sm whitespace-pre-wrap">
                {#if isExpanded || comp.response2.length <= 200}
                  {comp.response2}
                {:else}
                  {truncateText(comp.response2)}
                  <button 
                    on:click={() => toggleExpanded(`${compId}-resp2`)}
                    class="ml-2 text-blue-600 dark:text-blue-400 hover:underline text-sm"
                  >
                    Show more
                  </button>
                {/if}
              </div>
            </div>
          </div>

          <!-- Voting Reasoning -->
          {#if comp.votes && Object.keys(comp.votes).length > 0}
            {@const votingText = formatVotes(comp.votes)}
            <div class="p-6 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
              <h5 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Voter Reasoning</h5>
              <div class="text-gray-900 dark:text-gray-100 text-sm whitespace-pre-wrap">
                {#if isExpanded || votingText.length <= 200}
                  {votingText}
                {:else}
                  {truncateText(votingText)}
                  <button 
                    on:click={() => toggleExpanded(`${compId}-votes`)}
                    class="ml-2 text-blue-600 dark:text-blue-400 hover:underline text-sm"
                  >
                    Show more
                  </button>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      {/each}

      <!-- Load More Button -->
      {#if displayedComparisons.length < filteredComparisons.length}
        <div class="text-center">
          <button 
            on:click={loadMore}
            class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Load More ({filteredComparisons.length - displayedComparisons.length} remaining)
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div> 