"""
Dynamic project discovery and CSV logging system.

This module provides functionality to:
1. Discover FlipsideCrypto GitHub repositories automatically
2. Log cache status and project metadata to CSV
3. Manage project availability based on cache and discovery status
"""
import csv
import json
import os
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

import aiohttp



class ProjectDiscoveryManager:
    """Manages dynamic project discovery and CSV logging."""
    
    def __init__(self, cache_dir: str, csv_log_path: Optional[str] = None, github_token: Optional[str] = None, cache_ttl_seconds: int = 86400):
        self.cache_dir = Path(cache_dir)
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.cache_ttl_seconds = cache_ttl_seconds
        
        # Default CSV log path in cache directory
        if csv_log_path is None:
            csv_log_path = self.cache_dir / "project_discovery.csv"
        
        self.csv_log_path = Path(csv_log_path)
        self.csv_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV if it doesn't exist
        self._initialize_csv()
        
        # Rate limit tracking
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if it doesn't exist."""
        if not self.csv_log_path.exists():
            headers = [
                "resource_id",
                "name", 
                "blockchain",
                "category",
                "aliases",
                "location",
                "cached_at",
                "status",
                "error",
                "discovered_at",
                "has_docs_branch"
            ]
            
            with open(self.csv_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            
            logger.info(f"Initialized project discovery CSV at {self.csv_log_path}")
    
    def update_cache_status(self, resource_id: str, status: str, error: Optional[str] = None):
        """Update cache status for a resource in the CSV log."""
        try:
            # Read existing data
            existing_data = self._read_csv_data()
            
            # Find or create entry for this resource
            found = False
            for row in existing_data:
                if row.get('resource_id') == resource_id:
                    row['cached_at'] = datetime.now(timezone.utc).isoformat()
                    row['status'] = status
                    row['error'] = error or ''
                    found = True
                    break
            
            if not found:
                # Create new entry with minimal data
                new_row = {
                    'resource_id': resource_id,
                    'name': self._generate_name_from_id(resource_id),
                    'blockchain': self._extract_blockchain_from_id(resource_id),
                    'category': '',
                    'aliases': '',
                    'location': f'FlipsideCrypto/{resource_id}',
                    'cached_at': datetime.now(timezone.utc).isoformat(),
                    'status': status,
                    'error': error or '',
                    'discovered_at': '',
                    'has_docs_branch': ''
                }
                existing_data.append(new_row)
            
            # Write back to CSV
            self._write_csv_data(existing_data)
            logger.info(f"Updated cache status for {resource_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error updating cache status for {resource_id}: {e}")
    
    def _is_cache_valid(self, project_id: str) -> bool:
        """Check if cached artifacts are still valid for a project."""
        cache_meta_path = self.cache_dir / project_id / "cache_meta.json"
        
        if not cache_meta_path.exists():
            return False
        
        try:
            with open(cache_meta_path, 'r') as f:
                meta = json.load(f)
            
            # Check if cache has error status
            if meta.get('status') == 'error':
                return False
            
            cached_time = datetime.fromisoformat(meta['cached_at'])
            now = datetime.now(timezone.utc)
            age_seconds = (now - cached_time).total_seconds()
            
            return age_seconds < self.cache_ttl_seconds
        except Exception as e:
            logger.warning(f"Error reading cache metadata for {project_id}: {e}")
            return False
    
    def _generate_name_from_id(self, resource_id: str) -> str:
        """Generate a human-readable name from resource ID."""
        if resource_id.endswith('-models'):
            base_name = resource_id.replace('-models', '')
            return f"{base_name.title()} Models"
        return resource_id.replace('-', ' ').title()
    
    def _extract_blockchain_from_id(self, resource_id: str) -> str:
        """Extract blockchain name from resource ID."""
        if resource_id.endswith('-models'):
            return resource_id.replace('-models', '')
        return resource_id
    
    async def discover_flipside_projects(self, skip_valid_cache: bool = False, force_refresh: bool = False, specific_projects: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Discover FlipsideCrypto repositories that follow the <project>-models pattern.
        
        Args:
            skip_valid_cache: If True, skip docs branch checks for projects with valid cache
            force_refresh: If True, check all projects regardless of cache (overrides skip_valid_cache)
            specific_projects: If provided, only discover these specific project IDs
        """
        logger.info("Starting FlipsideCrypto project discovery")
        
        try:
            # Get all FlipsideCrypto repositories
            repos = await self._get_flipside_repositories()
            
            # Filter for *-models repositories
            model_repos = [repo for repo in repos if repo['name'].endswith('-models')]
            logger.info(f"Found {len(model_repos)} potential model repositories")
            
            # Filter to specific projects if requested
            if specific_projects:
                model_repos = [repo for repo in model_repos if repo['name'] in specific_projects]
                logger.info(f"Filtered to {len(model_repos)} specific requested repositories: {[r['name'] for r in model_repos]}")
            
            # Optimization: if skip_valid_cache is enabled and force_refresh is False,
            # skip docs branch checks for projects with valid cache
            repos_to_check = []
            repos_skipped_cache = []
            
            if skip_valid_cache and not force_refresh:
                for repo in model_repos:
                    if self._is_cache_valid(repo['name']):
                        repos_skipped_cache.append(repo)
                        logger.debug(f"Skipping docs branch check for {repo['name']} (valid cache)")
                    else:
                        repos_to_check.append(repo)
                
                logger.info(f"Cache optimization: checking docs branch for {len(repos_to_check)} repos, skipping {len(repos_skipped_cache)} with valid cache")
            else:
                repos_to_check = model_repos
                logger.info(f"Checking docs branch for all {len(repos_to_check)} repositories")
            
            # Check which ones have /docs branch
            valid_projects = []
            
            # First, add projects we skipped due to valid cache (we know they're valid)
            for repo in repos_skipped_cache:
                project_data = {
                    'resource_id': repo['name'],
                    'name': self._generate_name_from_id(repo['name']),
                    'blockchain': self._extract_blockchain_from_id(repo['name']),
                    'category': self._categorize_blockchain(self._extract_blockchain_from_id(repo['name'])),
                    'aliases': self._generate_aliases(repo['name']),
                    'location': repo['full_name'],
                    'cached_at': '',
                    'status': '',
                    'error': '',
                    'discovered_at': datetime.now(timezone.utc).isoformat(),
                    'has_docs_branch': 'True'  # We assume valid cache means docs branch exists
                }
                valid_projects.append(project_data)
            
            # Now check docs branch for remaining repos
            for repo in repos_to_check:
                has_docs = await self._check_docs_branch(repo['full_name'])
                
                project_data = {
                    'resource_id': repo['name'],
                    'name': self._generate_name_from_id(repo['name']),
                    'blockchain': self._extract_blockchain_from_id(repo['name']),
                    'category': self._categorize_blockchain(self._extract_blockchain_from_id(repo['name'])),
                    'aliases': self._generate_aliases(repo['name']),
                    'location': repo['full_name'],
                    'cached_at': '',
                    'status': '',
                    'error': '',
                    'discovered_at': datetime.now(timezone.utc).isoformat(),
                    'has_docs_branch': str(has_docs)
                }
                
                valid_projects.append(project_data)
                
                if has_docs:
                    logger.info(f"✓ {repo['name']} has docs branch")
                else:
                    logger.info(f"✗ {repo['name']} missing docs branch")
            
            # Update CSV with discovered projects
            await self._update_discovered_projects(valid_projects)
            
            logger.info(f"Discovery completed: {len(valid_projects)} projects found")
            return valid_projects
            
        except Exception as e:
            logger.error(f"Error during project discovery: {e}")
            return []
    
    async def _get_flipside_repositories(self) -> List[Dict[str, Any]]:
        """Get all repositories from FlipsideCrypto organization."""
        repos = []
        page = 1
        per_page = 100
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"https://api.github.com/orgs/FlipsideCrypto/repos?page={page}&per_page={per_page}"
                
                # Prepare headers with authentication if available
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                async with session.get(url, headers=headers) as response:
                    # Check rate limit headers
                    self._update_rate_limit_info(response.headers)
                    
                    response_text = await response.text()
                    
                    if response.status == 403 and 'rate limit exceeded' in response_text.lower():
                        reset_time = self.rate_limit_reset
                        if reset_time:
                            wait_seconds = max(0, reset_time - datetime.now(timezone.utc).timestamp())
                            logger.warning(f"Rate limit exceeded. Waiting {wait_seconds:.0f} seconds until reset...")
                            await asyncio.sleep(wait_seconds + 1)  # Add 1 second buffer
                            continue
                        else:
                            logger.error("Rate limit exceeded but no reset time available")
                            break
                    
                    if response.status != 200:
                        logger.error(f"Failed to fetch FlipsideCrypto repos: {response.status}. Error: {response_text}")
                        break
                    
                    page_repos = await response.json()
                    if not page_repos:
                        break
                    
                    repos.extend(page_repos)
                    
                    if len(page_repos) < per_page:
                        break
                    
                    page += 1
                    
                    # Add small delay between requests to be respectful
                    await asyncio.sleep(0.1)
        
        logger.info(f"Found {len(repos)} total FlipsideCrypto repositories")
        return repos
    
    def _update_rate_limit_info(self, headers):
        """Update rate limit information from response headers."""
        try:
            remaining = headers.get('X-RateLimit-Remaining')
            if remaining is not None:
                self.rate_limit_remaining = int(remaining)
            
            reset = headers.get('X-RateLimit-Reset')
            if reset is not None:
                self.rate_limit_reset = int(reset)
                
            if self.rate_limit_remaining is not None:
                logger.debug(f"Rate limit remaining: {self.rate_limit_remaining}")
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing rate limit headers: {e}")
    
    async def _check_docs_branch(self, repo_full_name: str) -> bool:
        """Check if a repository has a 'docs' branch."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.github.com/repos/{repo_full_name}/branches/docs"
                
                # Prepare headers with authentication if available
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                async with session.get(url, headers=headers) as response:
                    # Check rate limit headers
                    self._update_rate_limit_info(response.headers)
                    
                    response_text = await response.text()
                    
                    if response.status == 403 and 'rate limit exceeded' in response_text.lower():
                        reset_time = self.rate_limit_reset
                        if reset_time:
                            wait_seconds = max(0, reset_time - datetime.now(timezone.utc).timestamp())
                            logger.warning(f"Rate limit exceeded while checking docs branch. Waiting {wait_seconds:.0f} seconds...")
                            await asyncio.sleep(wait_seconds + 1)
                            # Retry once after waiting
                            async with session.get(url, headers=headers) as retry_response:
                                return retry_response.status == 200
                        else:
                            logger.error("Rate limit exceeded but no reset time available")
                            return False
                    
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"Error checking docs branch for {repo_full_name}: {e}")
            return False
    
    def _categorize_blockchain(self, blockchain: str) -> str:
        """Categorize blockchain by type."""
        categories = {
            'l1': ['bitcoin', 'avalanche', 'near', 'flow', 'stellar', 'ton', 'aleo', 'aptos', 'movement'],
            'evm': ['ethereum', 'arbitrum', 'optimism', 'polygon', 'base', 'bsc', 'gnosis', 'mantle', 'blast', 'aurora', 'boba', 'ronin', 'ink', 'swell', 'kaia', 'rise', 'monad', 'core', 'mezo'],
            'ibc': ['cosmos', 'osmosis', 'terra', 'thorchain', 'axelar', 'maya'],
            'svm': ['solana', 'eclipse'],
            'multi-chain': ['crosschain', 'external'],
            'internal': ['kairos']
        }
        
        for category, blockchains in categories.items():
            if blockchain.lower() in blockchains:
                return category
        
        return 'unknown'
    
    def _generate_aliases(self, resource_id: str) -> str:
        """Generate pipe-separated aliases for a resource."""
        aliases = [resource_id]
        
        if resource_id.endswith('-models'):
            base_name = resource_id.replace('-models', '')
            aliases.extend([
                base_name,
                f"{base_name}_models",
                f"{base_name}-models"
            ])
        
        # Add blockchain-specific abbreviations
        blockchain = self._extract_blockchain_from_id(resource_id)
        abbrevs = {
            'bitcoin': ['btc'],
            'ethereum': ['eth'],
            'polygon': ['matic', 'poly'], 
            'avalanche': ['avax'],
            'bsc': ['bnb', 'binance'],
            'solana': ['sol'],
            'arbitrum': ['arb'],
            'optimism': ['op']
        }
        
        if blockchain in abbrevs:
            aliases.extend(abbrevs[blockchain])
        
        return '|'.join(list(set(aliases)))
    
    async def _update_discovered_projects(self, projects: List[Dict[str, Any]]):
        """Update CSV with discovered projects, preserving cache status."""
        try:
            # Read existing data to preserve cache status
            existing_data = self._read_csv_data()
            existing_by_id = {row['resource_id']: row for row in existing_data}
            
            # Update discovered projects with existing cache status
            for project in projects:
                resource_id = project['resource_id']
                if resource_id in existing_by_id:
                    # Preserve cache status from existing data
                    existing_row = existing_by_id[resource_id]
                    project['cached_at'] = existing_row.get('cached_at', '')
                    project['status'] = existing_row.get('status', '')
                    project['error'] = existing_row.get('error', '')
            
            # Write updated data
            self._write_csv_data(projects)
            logger.info(f"Updated CSV with {len(projects)} discovered projects")
            
        except Exception as e:
            logger.error(f"Error updating discovered projects: {e}")
    
    def _read_csv_data(self) -> List[Dict[str, str]]:
        """Read CSV data as list of dictionaries."""
        data = []
        
        if not self.csv_log_path.exists():
            return data
        
        try:
            with open(self.csv_log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
        except Exception as e:
            logger.error(f"Error reading CSV data: {e}")
        
        return data
    
    def _write_csv_data(self, data: List[Dict[str, str]]):
        """Write data to CSV file."""
        if not data:
            return
        
        try:
            headers = [
                "resource_id",
                "name", 
                "blockchain",
                "category",
                "aliases",
                "location",
                "cached_at",
                "status",
                "error",
                "discovered_at",
                "has_docs_branch"
            ]
            
            with open(self.csv_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
                
        except Exception as e:
            logger.error(f"Error writing CSV data: {e}")
    
    def get_available_projects(self, require_cache: bool = False, require_docs_branch: bool = True) -> List[Dict[str, Any]]:
        """Get list of available projects based on discovery and cache status."""
        data = self._read_csv_data()
        available = []
        
        for row in data:
            # Filter based on requirements
            if require_docs_branch and row.get('has_docs_branch') != 'True':
                continue
                
            if require_cache and row.get('status') != 'success':
                continue
            
            available.append(row)
        
        logger.info(f"Found {len(available)} available projects (require_cache={require_cache}, require_docs_branch={require_docs_branch})")
        return available
    
    def get_cache_status_summary(self) -> Dict[str, Any]:
        """Get summary of cache status across all projects."""
        data = self._read_csv_data()
        
        total = len(data)
        successful = sum(1 for row in data if row.get('status') == 'success')
        failed = sum(1 for row in data if row.get('status') == 'error')
        uncached = total - successful - failed
        
        return {
            'total_projects': total,
            'successful_cache': successful,
            'failed_cache': failed,
            'uncached': uncached,
            'cache_success_rate': successful / total if total > 0 else 0
        }