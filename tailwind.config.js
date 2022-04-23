const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
    future: {
    },
    content: [
        "./templates/**/*.html"
      ],
    theme: {
        extend: {
            colors: {
                transparent: 'transparent',
                current: 'currentColor',
                blue: {
                    light: '#f4f7fb',
                    DEFAULT: '#99c1f1',
                    dark: '#1b5eb4',
                }
            },
            fontFamily: {
                sans: ['Rubik'],
            },
        },
    },
    variants: {},
    plugins: [],
}
