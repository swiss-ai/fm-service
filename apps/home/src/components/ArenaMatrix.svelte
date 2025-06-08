<script>
  import { onMount } from 'svelte';
  import { getModelLogo } from '@lib/modelLogos';
  
  export let matrixData = {};
  
  let models = [];
  let matrix = [];
  let hoveredCell = null;
  
  $: {
    if (matrixData && Object.keys(matrixData).length > 0) {
      models = Object.keys(matrixData);
      // Create the matrix with win rates
      matrix = models.map(model1 => 
        models.map(model2 => {
          if (model1 === model2) return 0.5; // Diagonal cells
          const wins = matrixData[model1]?.[model2] || 0;
          const total = wins + (matrixData[model2]?.[model1] || 0);
          return total > 0 ? wins / total : 0.5;
        })
      );
    }
  }
  
  function getCellColor(winRate) {
    if (winRate === 0.5) return 'bg-gray-100 dark:bg-gray-700'; // Diagonal
    
    // Create a more sophisticated color scale
    const intensity = Math.abs(winRate - 0.5) * 2; // 0 to 1
    
    if (winRate > 0.5) {
      // Green for wins (higher win rate)
      const opacity = Math.round(intensity * 9); // 1-9 for Tailwind opacity scale
      return `bg-green-${Math.max(1, Math.min(9, opacity * 100))} bg-opacity-${Math.max(10, Math.min(90, opacity * 10))}`;
    } else {
      // Red for losses (lower win rate)
      const opacity = Math.round(intensity * 9);
      return `bg-red-${Math.max(1, Math.min(9, opacity * 100))} bg-opacity-${Math.max(10, Math.min(90, opacity * 10))}`;
    }
  }
  
  function getCellColorStyle(winRate) {
    if (winRate === 0.5) return 'background-color: rgb(107 114 128 / 0.1)'; // Diagonal
    
    const intensity = Math.abs(winRate - 0.5) * 2;
    
    if (winRate > 0.5) {
      // Green gradient for wins
      const alpha = 0.2 + (intensity * 0.6); // 0.2 to 0.8
      return `background-color: rgba(34, 197, 94, ${alpha})`;
    } else {
      // Red gradient for losses  
      const alpha = 0.2 + (intensity * 0.6);
      return `background-color: rgba(239, 68, 68, ${alpha})`;
    }
  }
  
  function formatPercentage(winRate) {
    if (winRate === 0.5) return '—';
    return `${Math.round(winRate * 100)}%`;
  }
  
  function getTotalGames(model1, model2) {
    const wins1 = matrixData[model1]?.[model2] || 0;
    const wins2 = matrixData[model2]?.[model1] || 0;
    return wins1 + wins2;
  }
  
  function getDisplayName(modelName) {
    // Remove '-responses' suffix and clean up names
    return modelName.replace('-responses', '').replace(/apertus3-/, '');
  }
</script>

<div class="overflow-x-auto">
  {#if models.length > 0}
    <div class="min-w-max">
      <table class="w-full border-collapse">
        <thead>
          <tr>
            <th class="p-2 text-xs font-medium text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700"></th>
            {#each models as model}
              <th class="p-2 text-xs font-medium text-gray-900 dark:text-white border-b border-gray-200 dark:border-gray-700 max-w-32 overflow-hidden">
                <div class="transform -rotate-45 origin-left whitespace-nowrap text-left" style="transform-origin: left bottom;">
                  {getDisplayName(model)}
                </div>
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each models as model1, i}
            <tr>
              <td class="p-2 text-xs font-medium text-gray-900 dark:text-white border-r border-gray-200 dark:border-gray-700 max-w-32 overflow-hidden text-right">
                {getDisplayName(model1)}
              </td>
              {#each models as model2, j}
                <td 
                  class="relative p-0 border border-gray-200 dark:border-gray-700 w-12 h-12 cursor-pointer transition-all duration-200 hover:scale-110 hover:z-10 hover:shadow-lg"
                  style={getCellColorStyle(matrix[i][j])}
                  on:mouseenter={() => hoveredCell = {i, j, model1, model2, winRate: matrix[i][j], totalGames: getTotalGames(model1, model2)}}
                  on:mouseleave={() => hoveredCell = null}
                >
                  <div class="flex items-center justify-center h-full text-xs font-semibold text-gray-800 dark:text-gray-200">
                    {formatPercentage(matrix[i][j])}
                  </div>
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Legend -->
    <div class="mt-4 flex items-center justify-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
      <div class="flex items-center space-x-2">
        <div class="w-4 h-4 rounded" style="background-color: rgba(34, 197, 94, 0.6)"></div>
        <span>Higher Win Rate</span>
      </div>
      <div class="flex items-center space-x-2">
        <div class="w-4 h-4 rounded bg-gray-200 dark:bg-gray-600"></div>
        <span>Same Model</span>
      </div>
      <div class="flex items-center space-x-2">
        <div class="w-4 h-4 rounded" style="background-color: rgba(239, 68, 68, 0.6)"></div>
        <span>Lower Win Rate</span>
      </div>
    </div>
  {:else}
    <div class="text-center py-8 text-gray-500 dark:text-gray-400">
      Loading matrix data...
    </div>
  {/if}
</div>

<!-- Tooltip -->
{#if hoveredCell}
  <div class="fixed z-50 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-lg pointer-events-none"
       style="left: {hoveredCell.x || 0}px; top: {hoveredCell.y || 0}px;">
    <div class="font-semibold">{getDisplayName(hoveredCell.model1)} vs {getDisplayName(hoveredCell.model2)}</div>
    <div>Win Rate: {formatPercentage(hoveredCell.winRate)}</div>
    <div>Total Games: {hoveredCell.totalGames}</div>
  </div>
{/if} 