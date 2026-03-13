"""Jinja2 template rendering engine for email personalization."""

from __future__ import annotations

from jinja2 import Environment, BaseLoader, StrictUndefined, UndefinedError


class TemplateEngine:
    """Render email templates with contact-specific variables."""

    def __init__(self):
        self._env = Environment(
            loader=BaseLoader(),
            undefined=StrictUndefined,
            autoescape=False,  # emails need raw HTML
        )

    def render(self, template_str: str, variables: dict) -> str:
        """Render a template string with given variables.

        Variables like {{name}}, {{company}}, {{unsubscribe_url}} are replaced.
        Missing variables fall back to empty string to avoid send failures.
        """
        try:
            tpl = self._env.from_string(template_str)
            return tpl.render(**variables)
        except UndefinedError:
            # Graceful fallback: re-render with missing vars as ""
            safe_vars = dict(variables)

            class _Safe:
                def __getattr__(self, _):
                    return ""
                def __str__(self):
                    return ""

            env = Environment(loader=BaseLoader(), autoescape=False)
            tpl = env.from_string(template_str)
            return tpl.render(**safe_vars)

    def extract_variables(self, template_str: str) -> list[str]:
        """Extract variable names from a Jinja2 template string."""
        from jinja2 import meta
        env = Environment(loader=BaseLoader())
        ast = env.parse(template_str)
        return sorted(meta.find_undeclared_variables(ast))


# Global singleton
template_engine = TemplateEngine()
