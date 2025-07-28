#!/usr/bin/env python3
"""
Documentation Styles - Styling and formatting for generated documentation

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

from typing import Dict, Any, Optional
from enum import Enum


class DocumentationStyle(Enum):
    """Available documentation styles"""
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"
    PLAIN_TEXT = "plain"


class StyleFormatter:
    """Format documentation content with different styles"""
    
    def __init__(self, style: DocumentationStyle = DocumentationStyle.MARKDOWN):
        self.style = style
    
    def format_class_doc(self, class_info: Dict[str, Any]) -> str:
        """Format class documentation"""
        if self.style == DocumentationStyle.MARKDOWN:
            return self._format_class_markdown(class_info)
        elif self.style == DocumentationStyle.HTML:
            return self._format_class_html(class_info)
        else:
            return self._format_class_plain(class_info)
    
    def format_method_doc(self, method_info: Dict[str, Any]) -> str:
        """Format method documentation"""
        if self.style == DocumentationStyle.MARKDOWN:
            return self._format_method_markdown(method_info)
        elif self.style == DocumentationStyle.HTML:
            return self._format_method_html(method_info)
        else:
            return self._format_method_plain(method_info)
    
    def _format_class_markdown(self, class_info: Dict[str, Any]) -> str:
        """Format class documentation as Markdown"""
        name = class_info.get("name", "Unknown")
        description = class_info.get("description", "")
        
        return f"""## {name}

{description}

### Methods:
{self._format_methods_list_markdown(class_info.get("methods", []))}
"""
    
    def _format_class_html(self, class_info: Dict[str, Any]) -> str:
        """Format class documentation as HTML"""
        name = class_info.get("name", "Unknown")
        description = class_info.get("description", "")
        
        return f"""<h2>{name}</h2>
<p>{description}</p>
<h3>Methods:</h3>
{self._format_methods_list_html(class_info.get("methods", []))}
"""
    
    def _format_class_plain(self, class_info: Dict[str, Any]) -> str:
        """Format class documentation as plain text"""
        name = class_info.get("name", "Unknown")
        description = class_info.get("description", "")
        
        return f"""{name}
{'=' * len(name)}

{description}

Methods:
{self._format_methods_list_plain(class_info.get("methods", []))}
"""
    
    def _format_method_markdown(self, method_info: Dict[str, Any]) -> str:
        """Format method documentation as Markdown"""
        name = method_info.get("name", "unknown")
        params = method_info.get("parameters", [])
        returns = method_info.get("returns", "")
        
        param_str = ", ".join(f"`{p}`" for p in params)
        
        return f"""### {name}({param_str})

{method_info.get("description", "")}

**Returns:** {returns}
"""
    
    def _format_method_html(self, method_info: Dict[str, Any]) -> str:
        """Format method documentation as HTML"""
        name = method_info.get("name", "unknown")
        params = method_info.get("parameters", [])
        returns = method_info.get("returns", "")
        
        param_str = ", ".join(f"<code>{p}</code>" for p in params)
        
        return f"""<h3>{name}({param_str})</h3>
<p>{method_info.get("description", "")}</p>
<p><strong>Returns:</strong> {returns}</p>
"""
    
    def _format_method_plain(self, method_info: Dict[str, Any]) -> str:
        """Format method documentation as plain text"""
        name = method_info.get("name", "unknown")
        params = method_info.get("parameters", [])
        returns = method_info.get("returns", "")
        
        param_str = ", ".join(params)
        
        return f"""{name}({param_str})
{'-' * (len(name) + len(param_str) + 2)}

{method_info.get("description", "")}

Returns: {returns}
"""
    
    def _format_methods_list_markdown(self, methods: list) -> str:
        """Format methods list as Markdown"""
        return "\n".join(f"- `{m.get('name', 'unknown')}`" for m in methods)
    
    def _format_methods_list_html(self, methods: list) -> str:
        """Format methods list as HTML"""
        items = "\n".join(f"<li><code>{m.get('name', 'unknown')}</code></li>" for m in methods)
        return f"<ul>\n{items}\n</ul>"
    
    def _format_methods_list_plain(self, methods: list) -> str:
        """Format methods list as plain text"""
        return "\n".join(f"  - {m.get('name', 'unknown')}" for m in methods)