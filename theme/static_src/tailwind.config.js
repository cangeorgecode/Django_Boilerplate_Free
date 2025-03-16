module.exports = {
  content: [
    "../templates/**/*.html",
    "../../templates/**/*.html",
    "../../**/templates/**/*.html",
    "../../accounts/templates/account/**/*.html",
  ],
  theme: {
    extend: {
      spacing: {
        9: "2.25rem", // Add custom spacing value
        10: "2.5rem", // Add custom spacing value
        12: "3rem", // Add custom spacing value
        14: "3.5rem", // Add custom spacing value
        16: "4rem", // Add custom spacing value
      },
      backgroundClip: ['text'],
      backgroundImage: {
        'gradient-to-r': 'linear-gradient(to right, var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    require("@tailwindcss/aspect-ratio"),
    require("daisyui"),
  ],
};
