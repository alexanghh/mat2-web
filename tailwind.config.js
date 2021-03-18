const defaultTheme = require('tailwindcss/defaultTheme')

module.exports = {
    future: {
    },
    purge: [],
    theme: {
        extend: {
            colors: {
                blue: {
                    light: '#f4f7fb',
                    DEFAULT: '#99c1f1',
                    dark: '#1b5eb4',
                }
            },
            fontFamily: {
                sans: ['Inter var', ...defaultTheme.fontFamily.sans],
            },
        },
    },
    variants: {},
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
