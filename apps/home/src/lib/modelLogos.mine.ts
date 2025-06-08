// interface ModelLogoMap {
//   name: string;
//   pattern: RegExp;
//   logo: string;
// }

// // Map of model patterns to their logos
// const modelLogos: ModelLogoMap[] = [
//   {
//     name: "Meta",
//     pattern: /llama|opt/i,
//     logo: "https://cdn-avatars.huggingface.co/v1/production/uploads/646cf8084eefb026fb8fd8bc/oCTqufkdTkjyGodsx1vo1.png"
//   },
//   {
//     name: "Google",
//     pattern: /bert|t5|palm|gemma|google|gemini/i,
//     logo: "https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg"
//   },
//   {
//     name: "Hugging Face",
//     pattern: /.*/,  // Default fallback
//     logo: "https://huggingface.co/front/assets/huggingface_logo-noborder.svg"
//   },
// ];

// Map of organization names to their logos
const orgLogos: Record<string, string | null> = {
  'swissai': "https://avatars.githubusercontent.com/u/153931663?s=200",
  'bigscience': 'https://cdn-avatars.huggingface.co/v1/production/uploads/1634806038075-5df7e9e5da6d0311fd3d53f9.png',
  'CohereLabs': 'https://cdn-avatars.huggingface.co/v1/production/uploads/1678549441248-5e70f6048ce3c604d78fe133.png',
  'microsoft': 'https://cdn-avatars.huggingface.co/v1/production/uploads/1583646260758-5e64858c87403103f9f1055d.png',
  'Qwen': 'https://cdn-avatars.huggingface.co/v1/production/uploads/620760a26e3b7210c2ff1943/-s1gyJfvbE1RgO5iBeNOi.png',
  'croissantllm': 'https://cdn-avatars.huggingface.co/v1/production/uploads/60f2e021adf471cbdf8bb660/PuLzi_Evn-UPfTcZP0DSU.png',
  'mistralai': 'https://cdn-avatars.huggingface.co/v1/production/uploads/634c17653d11eaedd88b314d/9OgyfKstSZtbmsmuG8MbU.png',
  'google': 'https://cdn-avatars.huggingface.co/v1/production/uploads/5dd96eb166059660ed1ee413/WtA3YYitedOr9n02eHfJe.png',
  'meta-llama': 'https://cdn-avatars.huggingface.co/v1/production/uploads/646cf8084eefb026fb8fd8bc/oCTqufkdTkjyGodsx1vo1.png',
  'deepseek-ai': 'https://cdn-avatars.huggingface.co/v1/production/uploads/6538815d1bdb3c40db94fbfa/xMBly9PUMphrFVMxLX4kq.png',
  'hf': 'https://huggingface.co/front/assets/huggingface_logo-noborder.svg'
};

// Specific model mappings for arena data and custom models
const specificModels: Record<string, string | null> = {
  // Updated arena model names
  'gpt-4.1': 'https://cdn-avatars.huggingface.co/v1/production/uploads/1620805164087-5ec0135ded25d76864d553f1.png', // OpenAI
  'claude-3-5-sonnet-20241022': 'https://cdn-avatars.huggingface.co/v1/production/uploads/1670531762351-6200d0a443eb0913fa2df7cc.png', // Anthropic
  'gemini-1.5-flash-8b': orgLogos['google'],
  'gemini-1.5-flash': orgLogos['google'],
};

/**
 * Get the appropriate logo for a model based on its organization name
 */
export function getModelLogo(modelName: string): string | null {
  // Check specific model mappings first
  if (specificModels[modelName]) return specificModels[modelName];
  
  // If no slash, default to HF
  if (!modelName.includes('/')) return orgLogos['hf'];

  return orgLogos[modelName.split('/')[0]] || orgLogos['hf'];
}
