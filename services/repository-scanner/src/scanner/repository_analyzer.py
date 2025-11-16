"""
Repository Analyzer - Handles Git operations
"""
import os
import tempfile
import shutil
from typing import List, Optional
from git import Repo, GitCommandError
from pydriller import Repository
import logging

logger = logging.getLogger(__name__)


class RepositoryAnalyzer:
    """Analyzes Git repositories"""
    
    def __init__(self):
        self.clone_path = os.getenv("GIT_CLONE_PATH", "/tmp/repos")
        self.clone_timeout = int(os.getenv("GIT_CLONE_TIMEOUT", "300"))
        os.makedirs(self.clone_path, exist_ok=True)
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a Git repository
        
        Args:
            repo_url: Git repository URL
            branch: Branch to clone
            
        Returns:
            Local path to cloned repository
        """
        try:
            # Generate unique path for this repository
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            local_path = os.path.join(self.clone_path, f"{repo_name}_{branch}")
            
            # Remove existing directory if it exists
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
            
            logger.info(f"Cloning repository {repo_url} (branch: {branch}) to {local_path}")
            
            # Clone the repository
            Repo.clone_from(
                repo_url,
                local_path,
                branch=branch,
                depth=1  # Shallow clone for faster cloning
            )
            
            logger.info(f"Successfully cloned repository to {local_path}")
            return local_path
            
        except GitCommandError as e:
            logger.error(f"Git error cloning repository: {str(e)}")
            raise Exception(f"Failed to clone repository: {str(e)}")
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            raise
    
    def get_changed_files(self, repo_path: str, commit_sha: Optional[str] = None) -> List[str]:
        """
        Get list of changed files
        
        Args:
            repo_path: Path to Git repository
            commit_sha: Specific commit SHA (optional)
            
        Returns:
            List of changed file paths
        """
        try:
            changed_files = []
            
            if commit_sha:
                # Get files changed in specific commit
                for commit in Repository(repo_path, single=commit_sha).traverse_commits():
                    for modified_file in commit.modified_files:
                        changed_files.append(modified_file.new_path or modified_file.old_path)
            else:
                # Get files changed in last commit
                repo = Repo(repo_path)
                if len(repo.heads) > 0:
                    last_commit = repo.head.commit
                    if last_commit.parents:
                        parent = last_commit.parents[0]
                        diffs = parent.diff(last_commit)
                        for diff in diffs:
                            if diff.a_path:
                                changed_files.append(diff.a_path)
                            if diff.b_path and diff.b_path != diff.a_path:
                                changed_files.append(diff.b_path)
            
            logger.info(f"Found {len(changed_files)} changed files")
            return list(set(changed_files))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting changed files: {str(e)}")
            raise
    
    def get_file_content(self, repo_path: str, file_path: str) -> str:
        """
        Get content of a specific file
        
        Args:
            repo_path: Path to Git repository
            file_path: Relative path to file in repository
            
        Returns:
            File content as string
        """
        try:
            full_path = os.path.join(repo_path, file_path)
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return ""
    
    def get_commit_history(self, repo_path: str, max_commits: int = 10) -> List[dict]:
        """
        Get commit history
        
        Args:
            repo_path: Path to Git repository
            max_commits: Maximum number of commits to retrieve
            
        Returns:
            List of commit information
        """
        try:
            commits = []
            for commit in Repository(repo_path).traverse_commits():
                commits.append({
                    "sha": commit.hash,
                    "author": commit.author.name,
                    "date": commit.author_date.isoformat(),
                    "message": commit.msg,
                    "files_modified": len(commit.modified_files)
                })
                if len(commits) >= max_commits:
                    break
            
            return commits
            
        except Exception as e:
            logger.error(f"Error getting commit history: {str(e)}")
            return []
