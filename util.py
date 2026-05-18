from huggingface_hub import HfApi

def get_model_size(repo_id):
    api = HfApi()
    # Get repo info without downloading files
    repo_info = api.model_info(repo_id=repo_id, files_metadata=True)
    
    total_size_bytes = 0
    for file in repo_info.siblings:
        # 'size' attribute contains the file size in bytes
        size = file.size or 0
        total_size_bytes += size
        print(f"{file.rfilename}: {size / (1024**2):.2f} MB")
    
    print(f"\nTotal Download Size: {total_size_bytes / (1024**3):.2f} GB")

get_model_size("bert-base-uncased")