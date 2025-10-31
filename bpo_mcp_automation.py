#!/usr/bin/env python3
"""
BPO Project MCP Automation Scripts
Provides automated workflows for Label Studio integration with BPO document processing
"""
import os
import json
import asyncio
from pathlib import Path
from label_studio_mcp import (
    get_label_studio_projects_tool,
    get_label_studio_project_details_tool,
    list_label_studio_project_tasks_tool,
    import_label_studio_project_tasks_tool,
    create_label_studio_project_tool
)

# Set environment variables
os.environ['LABEL_STUDIO_API_KEY'] = '131a97106e49f9f2ed0db70d24f85092570753f3'
os.environ['LABEL_STUDIO_URL'] = 'http://localhost:8082'

class BPOMCPManager:
    """Manager class for BPO Label Studio MCP operations"""
    
    def __init__(self):
        self.project_id = None
        self.data_dir = Path("data/label-studio")
        
    def get_bpo_project(self):
        """Get or create the BPO project"""
        projects = get_label_studio_projects_tool()
        if isinstance(projects, str):
            projects = json.loads(projects)
            
        # Look for existing BPO project
        for project in projects:
            if "BPO" in project.get("title", "").upper():
                self.project_id = project["id"]
                print(f"Found existing BPO project: {project['title']} (ID: {self.project_id})")
                return self.project_id
                
        # Create new BPO project if none exists
        print("Creating new BPO project...")
        project_config = {
            "title": "BPO Intelligence Pipeline",
            "description": "Automated NER extraction pipeline for BPO industry intelligence",
            "label_config": self._get_bpo_label_config()
        }
        
        result = create_label_studio_project_tool(project_config)
        if isinstance(result, str):
            result = json.loads(result)
            
        self.project_id = result.get("id")
        print(f"Created BPO project with ID: {self.project_id}")
        return self.project_id
    
    def _get_bpo_label_config(self):
        """Get the BPO-specific label configuration"""
        return """
<View>
  <Style>
    .meta { color: #666; font-size: 12px; margin-bottom: 8px; }
    .section { margin: 10px 0 6px 0; font-weight: 600; }
  </Style>

  <!-- Read-only meta -->
  <View style="margin-bottom: 8px;">
    <Header value="BPO Intelligence Annotation" />
    <Header value="Source URL:" size="4" />
    <Text name="meta_url" value="$source_url" readonly="true" inline="true" className="meta" />
  </View>

  <!-- Span annotation target -->
  <Header value="Text" size="4" className="section" />
  <Text name="text" value="$text" granularities="word" highlightColor="#ffff0077" />

  <!-- Span entity labels -->
  <Header value="Entities" size="4" className="section" />
  <Labels name="label" toName="text" strokeWidth="1.5" opacity="0.9" allowEmpty="false">
    <Label value="COMPANY" background="#1f77b4" />
    <Label value="PERSON" background="#ff7f0e" />
    <Label value="DATE" background="#2ca02c" />
    <Label value="TECHNOLOGY" background="#d62728" />
    <Label value="MONEY" background="#9467bd" />
    <Label value="PERCENT" background="#8c564b" />
    <Label value="PRODUCT" background="#e377c2" />
    <Label value="COMPUTING_PRODUCT" background="#bcbd22" />
    <Label value="BUSINESS_TITLE" background="#17becf" />
    <Label value="LOCATION" background="#7f7f7f" />
    <Label value="TIME_RANGE" background="#aec7e8" />
    <Label value="TEMPORAL" background="#98df8a" />
    <Label value="SKILL" background="#ff9896" />
  </Labels>

  <!-- Relationships -->
  <Header value="Relationships" size="4" className="section" />
  <Relations name="rels" toName="text">
    <Relation value="ORL" />
  </Relations>

  <!-- Document-level categories -->
  <Header value="Document Categories" size="4" className="section" />
  <Choices name="industry" toName="text" choice="single" showInline="true" showOther="true">
    <Choice value="Banking_Financial_Services" />
    <Choice value="Insurance" />
    <Choice value="Healthcare" />
    <Choice value="Retail_Ecommerce" />
    <Choice value="Telecom" />
    <Choice value="Technology" />
    <Choice value="Energy_Utilities" />
    <Choice value="Government" />
    <Choice value="Travel_Hospitality" />
    <Choice value="Media_Entertainment" />
    <Choice value="Manufacturing" />
    <Choice value="Other" />
  </Choices>

  <Choices name="service" toName="text" choice="multiple" showInline="true" showOther="true">
    <Choice value="CX_Management" />
    <Choice value="Back_Office_Processing" />
    <Choice value="AI_Data_Services" />
    <Choice value="Consulting_Analytics_Technology" />
    <Choice value="Digital_CX_AI" />
    <Choice value="Trust_Safety" />
    <Choice value="Finance_Accounting" />
    <Choice value="Work_From_Home" />
    <Choice value="Other" />
  </Choices>

  <Choices name="content_type" toName="text" choice="single" showInline="true" showOther="true">
    <Choice value="Blog" />
    <Choice value="News" />
    <Choice value="Case_Study" />
    <Choice value="Press_Release" />
    <Choice value="Report_Whitepaper" />
    <Choice value="Landing_Page" />
    <Choice value="Product_Page" />
    <Choice value="Careers" />
    <Choice value="PDF" />
    <Choice value="Image" />
    <Choice value="Other" />
  </Choices>

  <TextArea name="notes" toName="text" rows="3" placeholder="Annotator notes (optional)" />
</View>
        """.strip()
    
    def import_sample_data(self, limit=100):
        """Import sample data from preprocessed files"""
        if not self.project_id:
            self.get_bpo_project()
            
        # Check for pre-annotated tasks
        tasks_file = self.data_dir / "tasks_with_predictions_5k.json"
        if tasks_file.exists():
            print(f"Importing pre-annotated tasks from {tasks_file}")
            with open(tasks_file, 'r') as f:
                tasks_data = json.load(f)
                
            # Limit the number of tasks
            if limit and limit < len(tasks_data):
                tasks_data = tasks_data[:limit]
                
            result = import_label_studio_project_tasks_tool(self.project_id, tasks_data)
            print(f"Import result: {result}")
            return result
        else:
            print(f"No pre-annotated tasks found at {tasks_file}")
            return None
    
    def get_project_status(self):
        """Get current project status and statistics"""
        if not self.project_id:
            self.get_bpo_project()
            
        # Get project details
        details = get_label_studio_project_details_tool(self.project_id)
        if isinstance(details, str):
            details = json.loads(details)
            
        # Get task list
        tasks = list_label_studio_project_tasks_tool(self.project_id)
        if isinstance(tasks, str):
            tasks = json.loads(tasks)
            
        status = {
            "project_id": self.project_id,
            "project_title": details.get("title", "Unknown"),
            "total_tasks": details.get("task_number", 0),
            "annotated_tasks": details.get("num_tasks_with_annotations", 0),
            "finished_tasks": details.get("finished_task_number", 0),
            "current_tasks": len(tasks) if tasks else 0
        }
        
        return status
    
    def print_status(self):
        """Print current project status"""
        status = self.get_project_status()
        print("\n" + "="*50)
        print("BPO Label Studio Project Status")
        print("="*50)
        print(f"Project: {status['project_title']} (ID: {status['project_id']})")
        print(f"Total Tasks: {status['total_tasks']}")
        print(f"Annotated Tasks: {status['annotated_tasks']}")
        print(f"Finished Tasks: {status['finished_tasks']}")
        print(f"Current Tasks in Queue: {status['current_tasks']}")
        print("="*50)

def main():
    """Main function for BPO MCP automation"""
    print("BPO Label Studio MCP Automation")
    print("="*40)
    
    manager = BPOMCPManager()
    
    # Get or create BPO project
    project_id = manager.get_bpo_project()
    
    # Print current status
    manager.print_status()
    
    # Import sample data (optional)
    import_sample = input("\nImport sample data? (y/n): ").lower().strip()
    if import_sample == 'y':
        limit = input("How many tasks to import? (default 100): ").strip()
        limit = int(limit) if limit.isdigit() else 100
        manager.import_sample_data(limit)
        manager.print_status()
    
    print("\nMCP automation ready!")
    print("You can now use natural language queries in Cursor to:")
    print("- List projects and tasks")
    print("- Import more data")
    print("- Check annotation progress")
    print("- Manage the BPO validation workflow")

if __name__ == "__main__":
    main()

