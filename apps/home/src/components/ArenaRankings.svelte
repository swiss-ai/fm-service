<script>
  import { getModelLogo } from '@lib/modelLogos';
  
  export let elosData = {};
  
  $: sortedRankings = Object.entries(elosData)
    .sort(([,a], [,b]) => b - a)
    .map(([model, elo], index) => ({
      rank: index + 1,
      model,
      elo: Math.round(elo),
      displayName: getDisplayName(model)
    }));
  
  function getDisplayName(modelName) {
    // Remove '-responses' suffix and clean up names
    return modelName.replace('-responses', '').replace(/apertus3-/, '');
  }
  
  function getRankIcon(rank) {
    switch(rank) {
      case 1: return '🥇';
      case 2: return '🥈'; 
      case 3: return '🥉';
      default: return '';
    }
  }
  
  function getRankColor(rank) {
    switch(rank) {
      case 1: return 'text-yellow-600 dark:text-yellow-400';
      case 2: return 'text-gray-500 dark:text-gray-400';
      case 3: return 'text-amber-600 dark:text-amber-400';
      default: return 'text-gray-700 dark:text-gray-300';
    }
  }
</script>

<div class="w-full">
  {#if sortedRankings.length > 0}
    <div class="overflow-x-auto">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-200 dark:border-gray-700">
            <th class="text-left py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">Rank</th>
            <th class="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">Model</th>
            <th class="text-right py-3 px-2 font-semibold text-gray-700 dark:text-gray-300">ELO Rating</th>
          </tr>
        </thead>
        <tbody>
          {#each sortedRankings as {rank, model, elo, displayName}}
            <tr class="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <td class="py-3 px-2">
                <div class="flex items-center space-x-2">
                  <span class="font-bold {getRankColor(rank)} text-lg">
                    #{rank}
                  </span>
                  <span class="text-lg">
                    {getRankIcon(rank)}
                  </span>
                </div>
              </td>
              <td class="py-3 px-4">
                <div class="flex items-center space-x-3">
                  {#if getModelLogo(model)}
                    <img src={getModelLogo(model)} alt="" class="w-6 h-6 rounded-sm flex-shrink-0" />
                  {/if}
                  <div>
                    <div class="font-medium text-gray-900 dark:text-gray-100">{displayName}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">{model}</div>
                  </div>
                </div>
              </td>
              <td class="py-3 px-2 text-right">
                <div class="font-mono font-semibold text-gray-900 dark:text-gray-100">
                  {elo}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    
    <div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
      <p>
        <strong>ELO Rating System:</strong> Higher ratings indicate better performance in head-to-head comparisons. 
        Ratings are calculated based on wins, losses, and the relative strength of opponents.
      </p>
    </div>
  {:else}
    <div class="text-center py-8 text-gray-500 dark:text-gray-400">
      Loading rankings data...
    </div>
  {/if}
</div> 