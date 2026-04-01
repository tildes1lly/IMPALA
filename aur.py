import httpx as hx

def search(query, expanded=False, return_type="pretty"):
    aur_data = hx.get(f"https://aur.archlinux.org/rpc/v5/search/{query[0]}").json()

    if return_type == "raw":
        return aur_data
    
    elif return_type == "pretty":
        results = []
        for result in aur_data["results"]:
            if (all(Query.lower() in result["Name"].lower() or (expanded and Query.lower() in result["Description"].lower()) for Query in query)):
                results.append({
                    "Repo": "[AUR]",
                    "Name": result["Name"],
                    "Version": result["Version"],
                    "Description": result["Description"]
                })
        return results
    else:
        print("Invalid return type. Use 'raw' or 'pretty'.")