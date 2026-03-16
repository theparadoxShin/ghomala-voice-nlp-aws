import json

with open("task_def_update.json") as f:
    td = json.load(f)

for env in td["containerDefinitions"][0]["environment"]:
    if env["name"] == "NOVA_LITE_MODEL_ID":
        env["value"] = "arn:aws:bedrock:us-east-1:685497515185:custom-model-deployment/0845rha0mvyz"
        break

with open("task_def_update.json", "w") as f:
    json.dump(td, f)

print("Updated task definition:")
for e in td["containerDefinitions"][0]["environment"]:
    print(f"  {e['name']} = {e['value']}")
