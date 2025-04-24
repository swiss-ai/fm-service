interface ModelLogoMap {
  name: string;
  pattern: RegExp;
  logo: string;
}

// Map of model patterns to their logos
const modelLogos: ModelLogoMap[] = [
  {
    name: "Meta",
    pattern: /llama|opt/i,
    logo: "https://cdn-avatars.huggingface.co/v1/production/uploads/646cf8084eefb026fb8fd8bc/oCTqufkdTkjyGodsx1vo1.png"
  },
  {
    name: "Google",
    pattern: /bert|t5|palm|gemma|google|gemini/i,
    logo: "https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg"
  },
  {
    name: "Hugging Face",
    pattern: /.*/,  // Default fallback
    logo: "https://huggingface.co/front/assets/huggingface_logo-noborder.svg"
  },
];

/**
 * Get the appropriate logo for a model based on its name
 */
export function getModelLogo(modelName: string): string {
  for (const model of modelLogos) {
    if (model.pattern.test(modelName)) {
      return model.logo;
    }
  }
  // Default to Hugging Face logo
  return modelLogos[0].logo;
}
