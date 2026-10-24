import os, requests, streamlit as st
st.set_page_config(page_title="TrustVault",page_icon="🔐",layout="wide")
API=os.getenv("TRUSTVAULT_API_URL","http://127.0.0.1:8000").rstrip("/")
st.title("🔐 TrustVault"); st.caption("Secure document sharing with role-based permissions and an audit trail.")
if "token" not in st.session_state: st.session_state.token=""
if "user" not in st.session_state: st.session_state.user=None
def headers(): return {"Authorization":f"Bearer {st.session_state.token}"} if st.session_state.token else {}
def api(method,path,**kwargs):
    try: return requests.request(method,API+path,headers=headers(),timeout=30,**kwargs)
    except requests.RequestException as e: st.error(f"Cannot connect to API {API}: {e}"); return None
with st.sidebar:
    st.subheader("Account")
    if not st.session_state.token:
        email=st.text_input("Email"); password=st.text_input("Password",type="password")
        if st.button("Log in",type="primary"):
            try:
                r=requests.post(API+"/auth/login",json={"email":email,"password":password},timeout=20)
                if r.ok: data=r.json(); st.session_state.token=data["access_token"]; st.session_state.user=data["user"]; st.rerun()
                else: st.error(r.text)
            except requests.RequestException as e: st.error(str(e))
    else:
        st.write(st.session_state.user["email"]); st.write("Role: "+st.session_state.user["role"])
        if st.button("Log out"): st.session_state.token=""; st.session_state.user=None; st.rerun()
    st.caption("API: "+API)
if not st.session_state.token:
    st.info("Log in using an account configured for this deployment. API documentation is available at the API /docs URL.")
    st.markdown("Demo accounts (local only): owner@example.com / ChangeMe-Owner-123!; viewer@example.com / ChangeMe-Viewer-123!; admin@example.com / ChangeMe-Admin-123!. Change these before deployment.")
    st.stop()
t1,t2,t3,t4=st.tabs(["Documents","Upload","Permissions","Admin audit"])
with t1:
    a,b,c=st.columns(3); q=a.text_input("Search"); category=b.text_input("Category"); owner=c.text_input("Owner email")
    r=api("GET","/documents",params={"q":q,"category":category,"owner_email":owner})
    if r is not None and r.ok:
        for d in r.json():
            with st.container(border=True):
                st.markdown(f"**{d['name']}** · {d['category']}"); st.caption(f"Owner: {d['owner_email']} · {d['original_filename']} · {d['size_bytes']} bytes")
                if d["description"]: st.write(d["description"])
                if st.button("Download",key=f"dl{d['id']}"):
                    dr=api("GET",f"/documents/{d['id']}/download")
                    if dr is not None and dr.ok: st.download_button("Save file",dr.content,file_name=d["original_filename"],mime=d["content_type"],key=f"save{d['id']}")
                    elif dr is not None: st.error(dr.text)
                if d["owner_id"]==st.session_state.user["id"]:
                    with st.expander("Edit metadata / delete"):
                        nn=st.text_input("Name",d["name"],key=f"n{d['id']}"); cc=st.text_input("Category",d["category"],key=f"c{d['id']}"); dd=st.text_area("Description",d["description"],key=f"d{d['id']}")
                        if st.button("Save metadata",key=f"up{d['id']}"):
                            ur=api("PATCH",f"/documents/{d['id']}",json={"name":nn,"category":cc,"description":dd}); st.success("Updated") if ur is not None and ur.ok else st.error(ur.text if ur is not None else "API error")
                        if st.button("Soft delete",key=f"del{d['id']}"):
                            dr=api("DELETE",f"/documents/{d['id']}"); st.success("Deleted") if dr is not None and dr.ok else st.error(dr.text if dr is not None else "API error"); st.rerun()
    elif r is not None: st.error(r.text)
with t2:
    with st.form("upload"):
        name=st.text_input("Document title"); cat=st.selectbox("Category",["General","Academic","Finance","Legal","Personal","Work","Other"]); desc=st.text_area("Description"); file=st.file_uploader("Choose file"); submit=st.form_submit_button("Upload")
    if submit:
        if not name.strip() or not file: st.warning("Enter a title and choose a file.")
        else:
            r=api("POST","/documents",data={"name":name,"category":cat,"description":desc},files={"file":(file.name,file.getvalue(),file.type or "application/octet-stream")})
            if r is not None and r.ok:
                st.success("Uploaded successfully!")
            else:
                st.error(r.text if r is not None else "API error")
with t3:
    st.write("Only the document owner can grant or revoke permissions. Find IDs in the API response or Swagger docs.")
    with st.form("grant"):
        did=st.number_input("Document ID",min_value=1,step=1); email=st.text_input("Recipient email"); permission=st.selectbox("Permission",["read","edit"]); grant=st.form_submit_button("Grant")
    if grant:
        r=api("POST",f"/documents/{int(did)}/permissions",json={"email":email,"permission":permission}); st.success(r.json()) if r is not None and r.ok else st.error(r.text if r is not None else "API error")
    with st.form("revoke"):
        did2=st.number_input("Document ID to revoke",min_value=1,step=1); uid=st.number_input("Recipient user ID",min_value=1,step=1); rev=st.form_submit_button("Revoke")
    if rev:
        r=api("DELETE",f"/documents/{int(did2)}/permissions/{int(uid)}"); st.success(r.json()) if r is not None and r.ok else st.error(r.text if r is not None else "API error")
with t4:
    if st.session_state.user["role"]!="admin": st.info("Admin role required.")
    else:
        r=api("GET","/admin/audit",params={"limit":100})
        if r is not None and r.ok: st.dataframe(r.json(),use_container_width=True)
        elif r is not None: st.error(r.text)
        if st.button("Verify audit chain"):
            vr=api("GET","/admin/audit/verify"); st.json(vr.json() if vr is not None and vr.ok else {"error":vr.text if vr is not None else "API error"})
