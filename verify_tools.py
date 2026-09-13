import model_tools
from model_tools import get_tool_definitions

tools = get_tool_definitions(enabled_toolsets=["hermes-telegram"], quiet_mode=True)
names = [t["function"]["name"] for t in tools]
print("LLM schema tools:", len(names))
print("gws_fetch_token hidden:", "gws_fetch_token" not in names)
print("gws_fetch_token sandbox-stub-kept:", "gws_fetch_token" in model_tools._last_resolved_tool_names)
print("dwd tools exposed:", sum(1 for n in names if n.startswith("gws_dwd_")))
print("oauth ops exposed:", sum(1 for n in names if n.startswith("gws_gmail") or n.startswith("gws_drive")))
print("gws_dwd_resolve:", "gws_dwd_resolve" in names)