This is a theme based on Bulma 1.0, a modern CSS framework based on Flexbox.

Bulma is a CSS-only framework (no JavaScript), which means this theme is lighter than Bootstrap-based themes.

## Features

- Clean, modern design
- Responsive navbar with mobile burger menu
- CSS-only (minimal JavaScript for navbar toggle)
- Bulma 1.0.4 via CDN

## Configuration

You can customize the navbar appearance in your `conf.py`:

```python
THEME_CONFIG = {
    'navbar_light': False,  # Set to True for light navbar
    'navbar_custom_bg': '',  # Custom background class, e.g., 'has-background-info'
}
```

## Note

This theme uses Bulma's native classes:
- `.is-active` for active states
- `.is-sr-only` for screen-reader-only content
- `.navbar-burger` for mobile menu toggle
- Bulma's `.section`, `.container`, `.columns`, `.column` for layout
