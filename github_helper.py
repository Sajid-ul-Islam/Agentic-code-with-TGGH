#!/usr/bin/env python3
"""
GitHub API Helper - Wrapper around PyGithub for common operations
"""

from github import Github, GithubException
import base64
from typing import List


class GitHubHelper:
    def __init__(self, token: str):
        self.gh = Github(token)
        self.user = self.gh.get_user()
    
    def get_user_repos(self) -> List[str]:
        """Get list of user's repositories"""
        repos = []
        for repo in self.user.get_repos():
            repos.append(repo.full_name)
        return repos
    
    def read_file(self, repo_name: str, file_path: str, branch: str = "main") -> str:
        """
        Read file content from repository
        
        Args:
            repo_name: "owner/repo" format
            file_path: Path to file
            branch: Branch name
        
        Returns:
            File content as string
        """
        try:
            repo = self.gh.get_repo(repo_name)
            contents = repo.get_contents(file_path, ref=branch)
            return contents.decoded_content.decode('utf-8')
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
    
    def edit_and_commit(
        self,
        repo_name: str,
        file_path: str,
        new_content: str,
        commit_message: str,
        branch: str = "main"
    ) -> str:
        """
        Edit file and commit changes
        
        Args:
            repo_name: "owner/repo" format
            file_path: Path to file
            new_content: New file content
            commit_message: Commit message
            branch: Branch to commit to
        
        Returns:
            Commit SHA
        """
        try:
            repo = self.gh.get_repo(repo_name)
            
            # Get existing file (to get SHA for update)
            try:
                contents = repo.get_contents(file_path, ref=branch)
                sha = contents.sha
                
                # Update existing file
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=sha,
                    branch=branch
                )
            except GithubException:
                # File doesn't exist, create it
                result = repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    branch=branch
                )
            
            return result['commit'].sha
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
    
    def list_files(self, repo_name: str, path: str = "", branch: str = "main") -> List[str]:
        """
        List files in repository directory
        
        Args:
            repo_name: "owner/repo" format
            path: Directory path (empty for root)
            branch: Branch name
        
        Returns:
            List of file paths
        """
        try:
            repo = self.gh.get_repo(repo_name)
            
            if not path:
                path = ""
            
            contents = repo.get_contents(path, ref=branch)
            
            files = []
            if isinstance(contents, list):
                for content in contents:
                    files.append(content.path)
            else:
                files.append(contents.path)
            
            return files
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
    
    def create_branch(
        self,
        repo_name: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> str:
        """
        Create a new branch
        
        Args:
            repo_name: "owner/repo" format
            branch_name: Name of new branch
            from_branch: Branch to create from
        
        Returns:
            Branch name
        """
        try:
            repo = self.gh.get_repo(repo_name)
            
            # Get the source branch's latest commit
            source_branch = repo.get_branch(from_branch)
            sha = source_branch.commit.sha
            
            # Create new branch
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=sha
            )
            
            return branch_name
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
    
    def get_commit_diff(
        self,
        repo_name: str,
        base_branch: str,
        head_branch: str
    ) -> str:
        """Get diff between two branches"""
        try:
            repo = self.gh.get_repo(repo_name)
            comparison = repo.compare(base_branch, head_branch)
            
            diff_text = f"Commits: {comparison.total_commits}\n"
            for commit in comparison.commits[:5]:  # Show first 5
                diff_text += f"\n- {commit.commit.message.split(chr(10))[0]}"
            
            if comparison.total_commits > 5:
                diff_text += f"\n... and {comparison.total_commits - 5} more"
            
            return diff_text
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
    
    def get_latest_commits(
        self,
        repo_name: str,
        branch: str = "main",
        count: int = 5
    ) -> str:
        """Get latest commits from branch"""
        try:
            repo = self.gh.get_repo(repo_name)
            commits = repo.get_commits(sha=branch)
            
            commit_text = ""
            for i, commit in enumerate(commits[:count]):
                msg = commit.commit.message.split('\n')[0]
                commit_text += f"{i+1}. {msg}\n   ({commit.sha[:7]})\n"
            
            return commit_text
        
        except GithubException as e:
            raise Exception(f"GitHub error: {e.data}")
