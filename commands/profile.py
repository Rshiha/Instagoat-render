def info(a,c):
 u=c.get("user")
 if not u:return "❌ Profile unavailable."
 return f"👤 PROFILE\nName: {getattr(u,'full_name','Unknown')}\nUsername: @{getattr(u,'username','Unknown')}\nID: {getattr(u,'pk',c.get('user_id'))}\nFollowers: {getattr(u,'follower_count','Unknown')}\nFollowing: {getattr(u,'following_count','Unknown')}\nPosts: {getattr(u,'media_count','Unknown')}\nPrivate: {getattr(u,'is_private','Unknown')}\nVerified: {getattr(u,'is_verified','Unknown')}\nBio: {getattr(u,'biography','') or '(empty)'}"
def profile(a,c): return info(a,c)
def uid(a,c): return "🆔 "+str(c.get("user_id","Unknown"))
def whois(a,c): return info(a,c)
PROFILE_COMMANDS={"info":info,"profile":profile,"uid":uid,"whois":whois}
