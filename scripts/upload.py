import os
import wandb
import yaml

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def upload_artifact(folder_path, artifact_name, project_name, artifact_type="dataset", job_type="upload-dataset"):
    run = wandb.init(project=project_name, job_type=job_type, name=artifact_name)
    artifact = wandb.Artifact(name=artifact_name, type=artifact_type)
    artifact.add_dir(folder_path)
    run.log_artifact(artifact)
    run.finish()
    print(f"Uploaded folder '{folder_path}' as W&B artifact '{artifact_name}'")

if __name__ == "__main__":
    config = load_config()
    folder_path = config["scraper"]["output_dir"]
    project_name = config["wandb"]["project"]

    wandb_data = config["wandb"]["data"]
    artifact_name = wandb_data["artifact_name"]
    artifact_type = wandb_data.get("artifact_type", "dataset")
    job_type = wandb_data.get("job_type", "upload-dataset")

    upload_artifact(folder_path, artifact_name, project_name, artifact_type, job_type)