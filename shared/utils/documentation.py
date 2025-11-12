"""
Comprehensive code documentation system with automatic generation and maintenance.
"""

import inspect
import ast
import os
import re
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FunctionDoc:
    """Documentation for a function."""
    name: str
    module: str
    signature: str
    docstring: str
    parameters: List[Dict[str, Any]]
    return_type: str
    return_description: str
    examples: List[str]
    exceptions: List[str]
    complexity: str
    line_number: int


@dataclass
class ClassDoc:
    """Documentation for a class."""
    name: str
    module: str
    docstring: str
    methods: List[FunctionDoc]
    attributes: List[Dict[str, Any]]
    inheritance: List[str]
    line_number: int


@dataclass
class ModuleDoc:
    """Documentation for a module."""
    name: str
    docstring: str
    functions: List[FunctionDoc]
    classes: List[ClassDoc]
    imports: List[str]
    constants: List[Dict[str, Any]]


class DocumentationGenerator:
    """Generate comprehensive documentation for code."""
    
    def __init__(self):
        self.documented_items = {}
    
    def generate_function_doc(self, func: Callable) -> FunctionDoc:
        """
        Generate documentation for a function.
        
        Args:
            func: Function to document
            
        Returns:
            Function documentation
        """
        # Get function info
        name = func.__name__
        module = func.__module__
        signature = str(inspect.signature(func))
        docstring = inspect.getdoc(func) or ""
        line_number = inspect.getsourcelines(func)[1]
        
        # Parse parameters
        parameters = self._parse_parameters(func)
        
        # Get return type
        return_type = self._get_return_type(func)
        return_description = self._extract_return_description(docstring)
        
        # Extract examples and exceptions
        examples = self._extract_examples(docstring)
        exceptions = self._extract_exceptions(docstring)
        
        # Estimate complexity
        complexity = self._estimate_complexity(func)
        
        return FunctionDoc(
            name=name,
            module=module,
            signature=signature,
            docstring=docstring,
            parameters=parameters,
            return_type=return_type,
            return_description=return_description,
            examples=examples,
            exceptions=exceptions,
            complexity=complexity,
            line_number=line_number
        )
    
    def generate_class_doc(self, cls: Type) -> ClassDoc:
        """
        Generate documentation for a class.
        
        Args:
            cls: Class to document
            
        Returns:
            Class documentation
        """
        # Get class info
        name = cls.__name__
        module = cls.__module__
        docstring = inspect.getdoc(cls) or ""
        line_number = inspect.getsourcelines(cls)[1]
        
        # Get methods
        methods = []
        for attr_name, attr_value in inspect.getmembers(cls):
            if inspect.isfunction(attr_value) and not attr_name.startswith('_'):
                methods.append(self.generate_function_doc(attr_value))
        
        # Get attributes
        attributes = self._parse_class_attributes(cls)
        
        # Get inheritance
        inheritance = [base.__name__ for base in cls.__bases__ if base != object]
        
        return ClassDoc(
            name=name,
            module=module,
            docstring=docstring,
            methods=methods,
            attributes=attributes,
            inheritance=inheritance,
            line_number=line_number
        )
    
    def generate_module_doc(self, module_path: str) -> ModuleDoc:
        """
        Generate documentation for a module.
        
        Args:
            module_path: Path to the module
            
        Returns:
            Module documentation
        """
        # Import module
        module_name = os.path.splitext(os.path.basename(module_path))[0]
        
        with open(module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse AST
        tree = ast.parse(source)
        
        # Extract module info
        docstring = ast.get_docstring(tree) or ""
        imports = self._extract_imports(tree)
        constants = self._extract_constants(tree)
        
        # Extract functions and classes
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_doc = self._ast_function_to_doc(node, module_name)
                if func_doc:
                    functions.append(func_doc)
            elif isinstance(node, ast.ClassDef):
                class_doc = self._ast_class_to_doc(node, module_name)
                if class_doc:
                    classes.append(class_doc)
        
        return ModuleDoc(
            name=module_name,
            docstring=docstring,
            functions=functions,
            classes=classes,
            imports=imports,
            constants=constants
        )
    
    def _parse_parameters(self, func: Callable) -> List[Dict[str, Any]]:
        """Parse function parameters."""
        parameters = []
        sig = inspect.signature(func)
        
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                "kind": str(param.kind),
                "description": ""
            }
            parameters.append(param_info)
        
        return parameters
    
    def _get_return_type(self, func: Callable) -> str:
        """Get function return type."""
        sig = inspect.signature(func)
        return_type = sig.return_annotation
        
        if return_type == inspect.Signature.empty:
            return "Any"
        
        return str(return_type)
    
    def _extract_return_description(self, docstring: str) -> str:
        """Extract return description from docstring."""
        lines = docstring.split('\n')
        in_returns = False
        return_lines = []
        
        for line in lines:
            if line.strip().lower().startswith('returns:'):
                in_returns = True
                continue
            elif in_returns and line.strip() and not line.startswith('    '):
                break
            elif in_returns:
                return_lines.append(line.strip())
        
        return ' '.join(return_lines).strip()
    
    def _extract_examples(self, docstring: str) -> List[str]:
        """Extract examples from docstring."""
        examples = []
        lines = docstring.split('\n')
        in_example = False
        current_example = []
        
        for line in lines:
            if 'example:' in line.lower() or 'examples:' in line.lower():
                in_example = True
                continue
            elif in_example and line.strip() and not line.startswith('    '):
                if current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                in_example = False
            elif in_example:
                current_example.append(line)
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples
    
    def _extract_exceptions(self, docstring: str) -> List[str]:
        """Extract exceptions from docstring."""
        exceptions = []
        lines = docstring.split('\n')
        
        for line in lines:
            if 'raises:' in line.lower() or 'exception:' in line.lower():
                # Extract exception names
                exception_match = re.search(r'(\w+Exception|\w+Error)', line)
                if exception_match:
                    exceptions.append(exception_match.group(1))
        
        return exceptions
    
    def _estimate_complexity(self, func: Callable) -> str:
        """Estimate function complexity."""
        try:
            source_lines = inspect.getsourcelines(func)[0]
            line_count = len(source_lines)
            
            if line_count < 10:
                return "Low"
            elif line_count < 50:
                return "Medium"
            else:
                return "High"
        except:
            return "Unknown"
    
    def _parse_class_attributes(self, cls: Type) -> List[Dict[str, Any]]:
        """Parse class attributes."""
        attributes = []
        
        for attr_name, attr_value in inspect.getmembers(cls):
            if not attr_name.startswith('_') and not inspect.isfunction(attr_value):
                attr_info = {
                    "name": attr_name,
                    "type": type(attr_value).__name__,
                    "value": str(attr_value)[:100] + "..." if len(str(attr_value)) > 100 else str(attr_value)
                }
                attributes.append(attr_info)
        
        return attributes
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract imports from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return imports
    
    def _extract_constants(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Extract constants from AST."""
        constants = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        constants.append({
                            "name": target.id,
                            "value": ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value)
                        })
        
        return constants
    
    def _ast_function_to_doc(self, node: ast.FunctionDef, module_name: str) -> Optional[FunctionDoc]:
        """Convert AST function to documentation."""
        try:
            return FunctionDoc(
                name=node.name,
                module=module_name,
                signature=f"def {node.name}(...)",
                docstring=ast.get_docstring(node) or "",
                parameters=[],
                return_type="Any",
                return_description="",
                examples=[],
                exceptions=[],
                complexity="Unknown",
                line_number=node.lineno
            )
        except:
            return None
    
    def _ast_class_to_doc(self, node: ast.ClassDef, module_name: str) -> Optional[ClassDoc]:
        """Convert AST class to documentation."""
        try:
            return ClassDoc(
                name=node.name,
                module=module_name,
                docstring=ast.get_docstring(node) or "",
                methods=[],
                attributes=[],
                inheritance=[base.id for base in node.bases if isinstance(base, ast.Name)],
                line_number=node.lineno
            )
        except:
            return None


class DocumentationFormatter:
    """Format documentation for different outputs."""
    
    @staticmethod
    def format_function_markdown(func_doc: FunctionDoc) -> str:
        """Format function documentation as Markdown."""
        md = f"## {func_doc.name}\n\n"
        
        if func_doc.docstring:
            md += f"{func_doc.docstring}\n\n"
        
        md += f"**Signature:** `{func_doc.signature}`\n\n"
        md += f"**Return Type:** `{func_doc.return_type}`\n\n"
        
        if func_doc.parameters:
            md += "**Parameters:**\n\n"
            for param in func_doc.parameters:
                md += f"- `{param['name']}` ({param['type']})"
                if param['default']:
                    md += f" = {param['default']}"
                md += f": {param['description']}\n"
            md += "\n"
        
        if func_doc.examples:
            md += "**Examples:**\n\n"
            for i, example in enumerate(func_doc.examples, 1):
                md += f"```python\n{example}\n```\n\n"
        
        if func_doc.exceptions:
            md += "**Exceptions:**\n\n"
            for exception in func_doc.exceptions:
                md += f"- `{exception}`\n"
            md += "\n"
        
        md += f"**Complexity:** {func_doc.complexity}\n\n"
        
        return md
    
    @staticmethod
    def format_class_markdown(class_doc: ClassDoc) -> str:
        """Format class documentation as Markdown."""
        md = f"## Class: {class_doc.name}\n\n"
        
        if class_doc.docstring:
            md += f"{class_doc.docstring}\n\n"
        
        if class_doc.inheritance:
            md += f"**Inherits from:** {', '.join(class_doc.inheritance)}\n\n"
        
        if class_doc.attributes:
            md += "**Attributes:**\n\n"
            for attr in class_doc.attributes:
                md += f"- `{attr['name']}` ({attr['type']}): {attr['value']}\n"
            md += "\n"
        
        if class_doc.methods:
            md += "**Methods:**\n\n"
            for method in class_doc.methods:
                md += f"- `{method.name}()`: {method.docstring.split('.')[0] if method.docstring else 'No description'}\n"
            md += "\n"
        
        return md
    
    @staticmethod
    def format_module_markdown(module_doc: ModuleDoc) -> str:
        """Format module documentation as Markdown."""
        md = f"# Module: {module_doc.name}\n\n"
        
        if module_doc.docstring:
            md += f"{module_doc.docstring}\n\n"
        
        if module_doc.imports:
            md += "**Imports:**\n\n"
            for imp in module_doc.imports:
                md += f"- `{imp}`\n"
            md += "\n"
        
        if module_doc.constants:
            md += "**Constants:**\n\n"
            for const in module_doc.constants:
                md += f"- `{const['name']}`: {const['value']}\n"
            md += "\n"
        
        if module_doc.classes:
            md += "## Classes\n\n"
            for class_doc in module_doc.classes:
                md += DocumentationFormatter.format_class_markdown(class_doc)
        
        if module_doc.functions:
            md += "## Functions\n\n"
            for func_doc in module_doc.functions:
                md += DocumentationFormatter.format_function_markdown(func_doc)
        
        return md


class DocumentationManager:
    """Manage documentation generation and maintenance."""
    
    def __init__(self, output_dir: str = "docs"):
        self.output_dir = output_dir
        self.generator = DocumentationGenerator()
        self.formatter = DocumentationFormatter()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_documentation(self, source_path: str) -> str:
        """
        Generate documentation for a source file.
        
        Args:
            source_path: Path to source file
            
        Returns:
            Path to generated documentation
        """
        try:
            # Generate module documentation
            module_doc = self.generator.generate_module_doc(source_path)
            
            # Format as Markdown
            markdown = self.formatter.format_module_markdown(module_doc)
            
            # Write to file
            output_path = os.path.join(
                self.output_dir,
                f"{module_doc.name}.md"
            )
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"Generated documentation: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating documentation for {source_path}: {e}")
            return ""
    
    def generate_project_documentation(self, source_dir: str) -> List[str]:
        """
        Generate documentation for entire project.
        
        Args:
            source_dir: Source directory
            
        Returns:
            List of generated documentation files
        """
        generated_files = []
        
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    file_path = os.path.join(root, file)
                    output_file = self.generate_documentation(file_path)
                    if output_file:
                        generated_files.append(output_file)
        
        return generated_files
    
    def create_index(self, documentation_files: List[str]) -> str:
        """
        Create index file for documentation.
        
        Args:
            documentation_files: List of documentation files
            
        Returns:
            Path to index file
        """
        index_path = os.path.join(self.output_dir, "README.md")
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Project Documentation\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Modules\n\n")
            
            for doc_file in documentation_files:
                module_name = os.path.splitext(os.path.basename(doc_file))[0]
                f.write(f"- [{module_name}]({os.path.basename(doc_file)})\n")
        
        return index_path


def auto_document_function(func: Callable) -> Callable:
    """
    Decorator to automatically document functions.
    
    Args:
        func: Function to document
        
    Returns:
        Decorated function
    """
    if not func.__doc__:
        # Generate basic documentation
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        
        doc = f"""
        {func.__name__}({', '.join(params)})
        
        Args:
"""
        for param in params:
            doc += f"            {param}: Parameter description\n"
        
        doc += """
        Returns:
            Return value description
        """
        
        func.__doc__ = doc.strip()
    
    return func


def auto_document_class(cls: Type) -> Type:
    """
    Decorator to automatically document classes.
    
    Args:
        cls: Class to document
        
    Returns:
        Decorated class
    """
    if not cls.__doc__:
        cls.__doc__ = f"{cls.__name__} class.\n\n    This class provides functionality for {cls.__name__.lower()} operations.\n    "
    
    return cls 