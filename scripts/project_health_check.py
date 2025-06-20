#!/usr/bin/env python3
"""
AiCockpit Project Health Check System
====================================

Advanced project health monitoring and AI-friendly diagnostics system
based on proven methodologies from the BluPow project.

This tool provides comprehensive analysis of:
- Project structure and organization
- Code quality and consistency
- Documentation completeness
- Configuration health
- Development environment status
- Backend/Frontend integration health

Usage:
    python3 scripts/project_health_check.py [--json] [--brief] [--category CATEGORY]
    
Categories: structure, code, docs, config, integration, all

Author: AiCockpit Development Team
License: GPL-3.0
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class HealthCheckResult:
    """Structured result object for health check operations."""
    category: str
    status: str  # HEALTHY, WARNING, ERROR
    score: int   # 0-100
    issues: List[str]
    recommendations: List[str]
    details: Dict[str, Any]
    timestamp: str

class AiCockpitHealthChecker:
    """Comprehensive health checker for AiCockpit project."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "acp_backend"
        self.frontend_root = project_root / "acp_frontend"
        
    def check_project_structure(self) -> HealthCheckResult:
        """Analyze project structure and organization."""
        issues = []
        recommendations = []
        details = {}
        score = 100
        
        # Essential directories
        essential_dirs = [
            "acp_backend", "acp_frontend", "tests", "scripts",
            "acp_backend/routers", "acp_backend/core", "acp_backend/models",
            "acp_frontend/src", "acp_frontend/src/components"
        ]
        
        missing_dirs = []
        for dir_path in essential_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            issues.append(f"Missing essential directories: {', '.join(missing_dirs)}")
            score -= len(missing_dirs) * 10
            recommendations.append("Create missing directory structure")
        
        # Essential files
        essential_files = [
            "README.md", "pyproject.toml", "acp_backend/main.py",
            "acp_frontend/package.json", "acp_frontend/next.config.js"
        ]
        
        missing_files = []
        for file_path in essential_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            issues.append(f"Missing essential files: {', '.join(missing_files)}")
            score -= len(missing_files) * 15
            recommendations.append("Create missing essential files")
        
        # Check for proper .gitignore
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
                required_patterns = [
                    "__pycache__", "node_modules", ".env", "*.pyc"
                ]
                missing_patterns = [p for p in required_patterns if p not in gitignore_content]
                if missing_patterns:
                    issues.append(f"Missing .gitignore patterns: {', '.join(missing_patterns)}")
                    score -= 5
        else:
            issues.append("Missing .gitignore file")
            score -= 10
        
        details.update({
            "total_directories": len(list(self.project_root.rglob("**/"))),
            "total_files": len(list(self.project_root.rglob("*"))),
            "backend_files": len(list(self.backend_root.rglob("*.py"))) if self.backend_root.exists() else 0,
            "frontend_files": len(list(self.frontend_root.rglob("*.tsx"))) + len(list(self.frontend_root.rglob("*.ts"))) if self.frontend_root.exists() else 0
        })
        
        status = "HEALTHY" if score >= 90 else "WARNING" if score >= 70 else "ERROR"
        
        return HealthCheckResult(
            category="structure",
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def check_code_quality(self) -> HealthCheckResult:
        """Analyze code quality and consistency."""
        issues = []
        recommendations = []
        details = {}
        score = 100
        
        # Check backend code quality
        if self.backend_root.exists():
            python_files = list(self.backend_root.rglob("*.py"))
            details["backend_python_files"] = len(python_files)
            
            # Check for basic code quality indicators
            for py_file in python_files[:10]:  # Sample first 10 files
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Check for basic quality indicators
                        if len(content.split('\n')) > 500:
                            issues.append(f"Large file detected: {py_file.name} ({len(content.split('\n'))} lines)")
                            score -= 2
                        
                        # Check for docstrings in classes/functions
                        if 'class ' in content or 'def ' in content:
                            if '"""' not in content and "'''" not in content:
                                issues.append(f"Missing docstrings in {py_file.name}")
                                score -= 1
                                
                except Exception as e:
                    issues.append(f"Could not analyze {py_file.name}: {str(e)}")
                    score -= 1
        else:
            issues.append("Backend directory not found")
            score -= 20
        
        # Check frontend code quality
        if self.frontend_root.exists():
            ts_files = list(self.frontend_root.rglob("*.ts")) + list(self.frontend_root.rglob("*.tsx"))
            details["frontend_typescript_files"] = len(ts_files)
            
            # Check package.json for essential dependencies
            package_json = self.frontend_root / "package.json"
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        package_data = json.load(f)
                        deps = package_data.get('dependencies', {})
                        essential_deps = ['next', 'react', 'typescript']
                        missing_deps = [dep for dep in essential_deps if dep not in deps]
                        if missing_deps:
                            issues.append(f"Missing essential frontend dependencies: {', '.join(missing_deps)}")
                            score -= 10
                except Exception as e:
                    issues.append(f"Could not parse package.json: {str(e)}")
                    score -= 5
            else:
                issues.append("Frontend package.json not found")
                score -= 15
        else:
            issues.append("Frontend directory not found")
            score -= 20
        
        # Check for linting configuration
        linting_configs = [".eslintrc.js", ".eslintrc.json", "eslint.config.mjs", "pyproject.toml"]
        found_configs = [config for config in linting_configs if (self.project_root / config).exists()]
        if not found_configs:
            issues.append("No linting configuration found")
            score -= 10
            recommendations.append("Set up linting configuration (ESLint for frontend, Ruff for backend)")
        else:
            details["linting_configs"] = found_configs
        
        status = "HEALTHY" if score >= 90 else "WARNING" if score >= 70 else "ERROR"
        
        return HealthCheckResult(
            category="code",
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def check_documentation(self) -> HealthCheckResult:
        """Analyze documentation completeness and quality."""
        issues = []
        recommendations = []
        details = {}
        score = 100
        
        # Check for essential documentation files
        essential_docs = [
            "README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md",
            "ACP Handoffdoc.txt"
        ]
        
        total_words = 0
        found_docs = []
        
        for doc in essential_docs:
            doc_path = self.project_root / doc
            if doc_path.exists():
                found_docs.append(doc)
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        word_count = len(content.split())
                        total_words += word_count
                        details[f"{doc}_words"] = word_count
                        
                        # Check for minimum content
                        if word_count < 100:
                            issues.append(f"{doc} appears incomplete ({word_count} words)")
                            score -= 5
                            
                except Exception as e:
                    issues.append(f"Could not read {doc}: {str(e)}")
                    score -= 2
            else:
                issues.append(f"Missing documentation: {doc}")
                score -= 15
                recommendations.append(f"Create {doc} with comprehensive content")
        
        details.update({
            "total_documentation_words": total_words,
            "found_documentation_files": found_docs,
            "documentation_coverage": f"{len(found_docs)}/{len(essential_docs)}"
        })
        
        # Check for inline code documentation
        if self.backend_root.exists():
            python_files = list(self.backend_root.rglob("*.py"))
            documented_files = 0
            for py_file in python_files[:20]:  # Sample
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '"""' in content or "'''" in content:
                            documented_files += 1
                except:
                    pass
            
            doc_ratio = documented_files / min(len(python_files), 20) if python_files else 0
            details["backend_documentation_ratio"] = f"{doc_ratio:.2%}"
            
            if doc_ratio < 0.5:
                issues.append("Low backend code documentation coverage")
                score -= 10
                recommendations.append("Add docstrings to Python modules, classes, and functions")
        
        status = "HEALTHY" if score >= 90 else "WARNING" if score >= 70 else "ERROR"
        
        return HealthCheckResult(
            category="documentation",
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def check_configuration(self) -> HealthCheckResult:
        """Analyze project configuration health."""
        issues = []
        recommendations = []
        details = {}
        score = 100
        
        # Check backend configuration
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'r') as f:
                    content = f.read()
                    details["pyproject_toml_present"] = True
                    
                    # Check for essential sections
                    essential_sections = ["[project]", "[build-system]", "[tool.ruff]", "[tool.black]"]
                    missing_sections = [section for section in essential_sections if section not in content]
                    if missing_sections:
                        issues.append(f"Missing pyproject.toml sections: {', '.join(missing_sections)}")
                        score -= len(missing_sections) * 5
                        
            except Exception as e:
                issues.append(f"Could not read pyproject.toml: {str(e)}")
                score -= 10
        else:
            issues.append("Missing pyproject.toml")
            score -= 20
            recommendations.append("Create pyproject.toml with project configuration")
        
        # Check frontend configuration
        if self.frontend_root.exists():
            frontend_configs = ["package.json", "next.config.js", "tsconfig.json"]
            missing_frontend_configs = []
            
            for config in frontend_configs:
                config_path = self.frontend_root / config
                if not config_path.exists():
                    missing_frontend_configs.append(config)
            
            if missing_frontend_configs:
                issues.append(f"Missing frontend configs: {', '.join(missing_frontend_configs)}")
                score -= len(missing_frontend_configs) * 10
                recommendations.append("Create missing frontend configuration files")
            
            details["frontend_configs_present"] = len(frontend_configs) - len(missing_frontend_configs)
        
        # Check environment configuration
        env_files = ["example.env", ".env.example", ".env"]
        found_env_files = [env for env in env_files if (self.project_root / env).exists()]
        details["environment_files"] = found_env_files
        
        if not found_env_files:
            issues.append("No environment configuration files found")
            score -= 15
            recommendations.append("Create example.env with required environment variables")
        
        status = "HEALTHY" if score >= 90 else "WARNING" if score >= 70 else "ERROR"
        
        return HealthCheckResult(
            category="configuration",
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def check_integration_health(self) -> HealthCheckResult:
        """Analyze backend/frontend integration health."""
        issues = []
        recommendations = []
        details = {}
        score = 100
        
        # Check if both backend and frontend exist
        backend_exists = self.backend_root.exists()
        frontend_exists = self.frontend_root.exists()
        
        details.update({
            "backend_present": backend_exists,
            "frontend_present": frontend_exists
        })
        
        if not backend_exists:
            issues.append("Backend directory missing")
            score -= 50
        
        if not frontend_exists:
            issues.append("Frontend directory missing")
            score -= 50
        
        if backend_exists and frontend_exists:
            # Check for API integration patterns
            frontend_src = self.frontend_root / "src"
            if frontend_src.exists():
                api_files = list(frontend_src.rglob("*api*")) + list(frontend_src.rglob("*client*"))
                details["frontend_api_files"] = len(api_files)
                
                if len(api_files) == 0:
                    issues.append("No API integration files found in frontend")
                    score -= 15
                    recommendations.append("Create API client modules for backend communication")
            
            # Check for shared types/interfaces
            backend_models = self.backend_root / "models"
            if backend_models.exists():
                model_files = list(backend_models.rglob("*.py"))
                details["backend_model_files"] = len(model_files)
            else:
                issues.append("Backend models directory not found")
                score -= 10
                recommendations.append("Create backend models directory for data structures")
            
            # Check for proper proxy configuration
            next_config = self.frontend_root / "next.config.js"
            if next_config.exists():
                try:
                    with open(next_config, 'r') as f:
                        content = f.read()
                        if "rewrites" in content or "proxy" in content:
                            details["frontend_proxy_configured"] = True
                        else:
                            issues.append("Frontend proxy configuration may be missing")
                            score -= 10
                            recommendations.append("Configure Next.js rewrites for backend API calls")
                except Exception as e:
                    issues.append(f"Could not analyze next.config.js: {str(e)}")
                    score -= 5
        
        status = "HEALTHY" if score >= 90 else "WARNING" if score >= 70 else "ERROR"
        
        return HealthCheckResult(
            category="integration",
            status=status,
            score=score,
            issues=issues,
            recommendations=recommendations,
            details=details,
            timestamp=datetime.now().isoformat()
        )
    
    def run_comprehensive_check(self, categories: Optional[List[str]] = None) -> Dict[str, HealthCheckResult]:
        """Run comprehensive health check across all categories."""
        all_categories = {
            "structure": self.check_project_structure,
            "code": self.check_code_quality,
            "documentation": self.check_documentation,
            "configuration": self.check_configuration,
            "integration": self.check_integration_health
        }
        
        if categories:
            categories_to_run = {k: v for k, v in all_categories.items() if k in categories}
        else:
            categories_to_run = all_categories
        
        results = {}
        for category, check_func in categories_to_run.items():
            try:
                results[category] = check_func()
            except Exception as e:
                results[category] = HealthCheckResult(
                    category=category,
                    status="ERROR",
                    score=0,
                    issues=[f"Health check failed: {str(e)}"],
                    recommendations=["Fix the underlying issue and retry health check"],
                    details={"error": str(e)},
                    timestamp=datetime.now().isoformat()
                )
        
        return results

def format_results_human(results: Dict[str, HealthCheckResult]) -> str:
    """Format results for human-readable output."""
    output = []
    output.append("🚀 AiCockpit Project Health Check Results")
    output.append("=" * 50)
    output.append("")
    
    overall_score = sum(result.score for result in results.values()) / len(results) if results else 0
    overall_status = "HEALTHY" if overall_score >= 90 else "WARNING" if overall_score >= 70 else "ERROR"
    
    # Status emoji mapping
    status_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "ERROR": "❌"}
    
    output.append(f"📊 Overall Health: {status_emoji.get(overall_status, '❓')} {overall_status} ({overall_score:.1f}/100)")
    output.append("")
    
    for category, result in results.items():
        emoji = status_emoji.get(result.status, '❓')
        output.append(f"{emoji} {category.upper()}: {result.status} ({result.score}/100)")
        
        if result.issues:
            output.append("   Issues:")
            for issue in result.issues:
                output.append(f"   • {issue}")
        
        if result.recommendations:
            output.append("   Recommendations:")
            for rec in result.recommendations:
                output.append(f"   → {rec}")
        
        output.append("")
    
    return "\n".join(output)

def format_results_brief(results: Dict[str, HealthCheckResult]) -> str:
    """Format results for brief output."""
    overall_score = sum(result.score for result in results.values()) / len(results) if results else 0
    overall_status = "HEALTHY" if overall_score >= 90 else "WARNING" if overall_score >= 70 else "ERROR"
    
    status_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "ERROR": "❌"}
    lines = [f"AiCockpit Health: {status_emoji.get(overall_status, '❓')} {overall_status} ({overall_score:.1f}/100)"]
    
    for category, result in results.items():
        emoji = status_emoji.get(result.status, '❓')
        lines.append(f"{category}: {emoji} {result.score}/100")
    
    return " | ".join(lines)

def main():
    """Main entry point for the health check system."""
    parser = argparse.ArgumentParser(
        description="AiCockpit Project Health Check System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/project_health_check.py
  python3 scripts/project_health_check.py --json
  python3 scripts/project_health_check.py --brief
  python3 scripts/project_health_check.py --category structure code
        """
    )
    
    parser.add_argument(
        "--json", 
        action="store_true", 
        help="Output results in JSON format (AI-friendly)"
    )
    parser.add_argument(
        "--brief", 
        action="store_true", 
        help="Output brief summary only"
    )
    parser.add_argument(
        "--category", 
        nargs="+", 
        choices=["structure", "code", "documentation", "configuration", "integration", "all"],
        help="Specific categories to check (default: all)"
    )
    
    args = parser.parse_args()
    
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Initialize health checker
    checker = AiCockpitHealthChecker(project_root)
    
    # Determine categories to check
    categories = None
    if args.category and "all" not in args.category:
        categories = args.category
    
    try:
        # Run health checks
        results = checker.run_comprehensive_check(categories)
        
        # Output results
        if args.json:
            # Convert to JSON-serializable format
            json_results = {k: asdict(v) for k, v in results.items()}
            print(json.dumps(json_results, indent=2))
        elif args.brief:
            print(format_results_brief(results))
        else:
            print(format_results_human(results))
        
        # Set exit code based on overall health
        overall_score = sum(result.score for result in results.values()) / len(results) if results else 0
        if overall_score < 70:
            sys.exit(1)  # Error exit code for CI/CD
        elif overall_score < 90:
            sys.exit(2)  # Warning exit code
        else:
            sys.exit(0)  # Success
            
    except Exception as e:
        if args.json:
            error_result = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(json.dumps(error_result, indent=2))
        else:
            print(f"❌ Health check failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 