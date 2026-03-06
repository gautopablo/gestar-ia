import os

import pandas as pd
import streamlit as st
from db_adapter import DBAdapter


# set_page_config solo cuando se ejecuta standalone
if __name__ == "__main__":
    st.set_page_config(page_title="Gestar Admin Maestros", layout="wide")


def get_secret(name, default=None):
    value = None
    try:
        if name in st.secrets:
            value = st.secrets.get(name)
    except Exception:
        value = None
    if value not in (None, ""):
        return value
    env_value = os.getenv(name)
    if env_value not in (None, ""):
        return env_value
    return default


def get_connection():
    return get_db_adapter().connect()


def get_db_adapter():
    mode = (get_secret("DB_MODE", "azure") or "azure").strip().lower()
    schema = get_secret("DB_SCHEMA", "gestar")
    sqlite_path = get_secret("SQLITE_PATH", "tickets_mvp.db")
    conn_str = get_secret("ODBC_CONN_STR")
    return DBAdapter(
        mode=mode,
        schema=schema,
        sqlite_path=sqlite_path,
        odbc_conn_str=conn_str,
    )


def qname(table_name):
    return get_db_adapter().qname(table_name)


def current_backend_label():
    return "SQLite" if get_db_adapter().is_sqlite else "Azure SQL"


def load_df(sql, params=()):
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def execute_many(statements):
    with get_connection() as conn:
        cur = conn.cursor()
        for sql, params in statements:
            cur.execute(sql, params)
        conn.commit()


def is_new_id(value):
    return pd.isna(value) or str(value).strip() == ""


def save_simple_table(
    df_original, df_edited, table, id_col, data_cols, soft_delete_col=None
):
    updates = []
    orig_ids = set(df_original[id_col].dropna().astype(int).tolist())
    edited_ids = set()

    for _, row in df_edited.iterrows():
        rid = row.get(id_col)
        values = [row.get(col) for col in data_cols]
        if is_new_id(rid):
            if all((v is None or str(v).strip() == "") for v in values):
                continue
            cols_sql = ", ".join(data_cols)
            qmarks = ", ".join(["?"] * len(data_cols))
            updates.append(
                (
                    f"INSERT INTO {qname(table)} ({cols_sql}) VALUES ({qmarks})",
                    tuple(values),
                )
            )
        else:
            rid_int = int(rid)
            edited_ids.add(rid_int)
            set_sql = ", ".join([f"{c} = ?" for c in data_cols])
            updates.append(
                (
                    f"UPDATE {qname(table)} SET {set_sql} WHERE {id_col} = ?",
                    tuple(values + [rid_int]),
                )
            )

    if soft_delete_col:
        removed_ids = orig_ids - edited_ids
        for rid in removed_ids:
            updates.append(
                (
                    f"UPDATE {qname(table)} SET {soft_delete_col} = 0 WHERE {id_col} = ?",
                    (rid,),
                )
            )

    execute_many(updates)


def area_editor():
    divisions = load_df(
        f"SELECT DivisionId, Nombre FROM {qname('Divisiones')} ORDER BY Nombre"
    )
    div_map = {r["Nombre"]: int(r["DivisionId"]) for _, r in divisions.iterrows()}
    div_names = list(div_map.keys())

    df = load_df(
        f"""
        SELECT a.AreaId, a.Nombre, a.DivisionId, d.Nombre AS Division, a.Activo
        FROM {qname("Areas")} a
        LEFT JOIN {qname("Divisiones")} d ON d.DivisionId = a.DivisionId
        ORDER BY a.AreaId
        """
    )
    view = df[["AreaId", "Nombre", "Division", "Activo"]].copy()
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Division": st.column_config.SelectboxColumn("Division", options=div_names),
            "Activo": st.column_config.CheckboxColumn("Activo"),
        },
        key="areas_editor",
    )
    if st.button("Guardar Areas", use_container_width=True):
        statements = []
        orig_ids = set(view["AreaId"].dropna().astype(int).tolist())
        edited_ids = set()
        for _, row in edited.iterrows():
            area_id = row.get("AreaId")
            nombre = row.get("Nombre")
            division_name = row.get("Division")
            activo = bool(row.get("Activo", True))
            if is_new_id(area_id):
                if not nombre or not division_name:
                    continue
                div_id = div_map.get(division_name)
                if div_id is None:
                    st.error(f"Division invalida: {division_name}")
                    return
                statements.append(
                    (
                        f"INSERT INTO {qname('Areas')} (Nombre, DivisionId, Activo) VALUES (?, ?, ?)",
                        (nombre, div_id, int(activo)),
                    )
                )
            else:
                area_id = int(area_id)
                edited_ids.add(area_id)
                div_id = div_map.get(division_name) if division_name else None
                statements.append(
                    (
                        f"UPDATE {qname('Areas')} SET Nombre = ?, DivisionId = ?, Activo = ? WHERE AreaId = ?",
                        (nombre, div_id, int(activo), area_id),
                    )
                )

        for rid in orig_ids - edited_ids:
            statements.append(
                (f"UPDATE {qname('Areas')} SET Activo = 0 WHERE AreaId = ?", (rid,))
            )
        execute_many(statements)
        st.success("Areas guardadas.")
        st.rerun()


def subcategory_editor():
    categorias = load_df(
        f"SELECT CategoriaId, Nombre FROM {qname('Categorias')} ORDER BY Nombre"
    )
    cat_map = {r["Nombre"]: int(r["CategoriaId"]) for _, r in categorias.iterrows()}
    cat_names = list(cat_map.keys())

    df = load_df(
        f"""
        SELECT s.SubcategoriaId, s.Nombre, s.CategoriaId, c.Nombre AS Categoria, s.Activo
        FROM {qname("Subcategorias")} s
        JOIN {qname("Categorias")} c ON c.CategoriaId = s.CategoriaId
        ORDER BY s.SubcategoriaId
        """
    )
    view = df[["SubcategoriaId", "Nombre", "Categoria", "Activo"]].copy()
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria", options=cat_names
            ),
            "Activo": st.column_config.CheckboxColumn("Activo"),
        },
        key="subcats_editor",
    )
    if st.button("Guardar Subcategorias", use_container_width=True):
        statements = []
        orig_ids = set(view["SubcategoriaId"].dropna().astype(int).tolist())
        edited_ids = set()
        for _, row in edited.iterrows():
            sub_id = row.get("SubcategoriaId")
            nombre = row.get("Nombre")
            categoria_name = row.get("Categoria")
            activo = bool(row.get("Activo", True))
            if is_new_id(sub_id):
                if not nombre or not categoria_name:
                    continue
                cat_id = cat_map.get(categoria_name)
                if cat_id is None:
                    st.error(f"Categoria invalida: {categoria_name}")
                    return
                statements.append(
                    (
                        f"INSERT INTO {qname('Subcategorias')} (Nombre, CategoriaId, Activo) VALUES (?, ?, ?)",
                        (nombre, cat_id, int(activo)),
                    )
                )
            else:
                sub_id = int(sub_id)
                edited_ids.add(sub_id)
                cat_id = cat_map.get(categoria_name) if categoria_name else None
                statements.append(
                    (
                        f"UPDATE {qname('Subcategorias')} SET Nombre = ?, CategoriaId = ?, Activo = ? WHERE SubcategoriaId = ?",
                        (nombre, cat_id, int(activo), sub_id),
                    )
                )

        for rid in orig_ids - edited_ids:
            statements.append(
                (
                    f"UPDATE {qname('Subcategorias')} SET Activo = 0 WHERE SubcategoriaId = ?",
                    (rid,),
                )
            )
        execute_many(statements)
        st.success("Subcategorias guardadas.")
        st.rerun()


def user_editor():
    # Detectar si existen columnas relacionales en Users
    adapter = get_db_adapter()
    with get_connection() as conn:
        user_cols = set(adapter.list_columns(conn, "Users"))
    has_area_id = "areaid" in user_cols
    has_division_id = "divisionid" in user_cols

    if not has_area_id and not has_division_id:
        df = load_df(
            f"SELECT UserId, Username, Email, Role, Active FROM {qname('Users')} ORDER BY UserId"
        )
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key="users"
        )
        if st.button("Guardar Users", use_container_width=True):
            save_simple_table(
                df,
                edited,
                "Users",
                "UserId",
                ["Username", "Email", "Role", "Active"],
                "Active",
            )
            st.success("Users guardados.")
            st.rerun()
        return

    areas_df = load_df(
        f"SELECT AreaId, Nombre FROM {qname('Areas')} WHERE Activo = 1 ORDER BY Nombre"
    )
    divs_df = load_df(
        f"SELECT DivisionId, Nombre FROM {qname('Divisiones')} WHERE Activo = 1 ORDER BY Nombre"
    )
    area_name_to_id = {r["Nombre"]: int(r["AreaId"]) for _, r in areas_df.iterrows()}
    div_name_to_id = {r["Nombre"]: int(r["DivisionId"]) for _, r in divs_df.iterrows()}
    area_options = [""] + list(area_name_to_id.keys())
    division_options = [""] + list(div_name_to_id.keys())

    select_area_name = "a.Nombre AS Area" if has_area_id else "NULL AS Area"
    select_div_name = "d.Nombre AS Division" if has_division_id else "NULL AS Division"
    select_area_id = "u.AreaId" if has_area_id else "NULL AS AreaId"
    select_div_id = "u.DivisionId" if has_division_id else "NULL AS DivisionId"

    df = load_df(
        f"""
        SELECT
            u.UserId, u.Username, u.Email, u.Role, u.Active,
            {select_area_id},
            {select_div_id},
            {select_area_name},
            {select_div_name}
        FROM {qname("Users")} u
        LEFT JOIN {qname("Areas")} a ON {"u.AreaId = a.AreaId" if has_area_id else "1=0"}
        LEFT JOIN {qname("Divisiones")} d ON {"u.DivisionId = d.DivisionId" if has_division_id else "1=0"}
        ORDER BY u.UserId
        """
    )

    view_cols = ["UserId", "Username", "Email", "Role", "Active", "Area", "Division"]
    view = df[view_cols].copy()
    role_options = ["Solicitante", "Analista", "Jefe", "Director", "Administrador"]
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Active": st.column_config.CheckboxColumn("Active"),
            "Role": st.column_config.SelectboxColumn("Rol", options=role_options),
            "Area": st.column_config.SelectboxColumn("Area", options=area_options),
            "Division": st.column_config.SelectboxColumn(
                "Division", options=division_options
            ),
        },
        key="users_editor",
    )

    if st.button("Guardar Users", use_container_width=True):
        statements = []
        orig_ids = set(df["UserId"].dropna().astype(int).tolist())
        edited_ids = set()

        for _, row in edited.iterrows():
            user_id = row.get("UserId")
            username = row.get("Username")
            email = row.get("Email")
            role = row.get("Role")
            active = int(bool(row.get("Active", True)))
            area_id = area_name_to_id.get(row.get("Area")) if has_area_id else None
            division_id = (
                div_name_to_id.get(row.get("Division")) if has_division_id else None
            )

            if is_new_id(user_id):
                if not username:
                    continue
                cols = ["Username", "Email", "Role", "Active"]
                vals = [username, email, role, active]
                if has_area_id:
                    cols.append("AreaId")
                    vals.append(area_id)
                if has_division_id:
                    cols.append("DivisionId")
                    vals.append(division_id)
                col_sql = ", ".join(cols)
                qmarks = ", ".join(["?"] * len(vals))
                statements.append(
                    (
                        f"INSERT INTO {qname('Users')} ({col_sql}) VALUES ({qmarks})",
                        tuple(vals),
                    )
                )
            else:
                user_id = int(user_id)
                edited_ids.add(user_id)
                sets = ["Username = ?", "Email = ?", "Role = ?", "Active = ?"]
                vals = [username, email, role, active]
                if has_area_id:
                    sets.append("AreaId = ?")
                    vals.append(area_id)
                if has_division_id:
                    sets.append("DivisionId = ?")
                    vals.append(division_id)
                set_sql = ", ".join(sets)
                statements.append(
                    (
                        f"UPDATE {qname('Users')} SET {set_sql} WHERE UserId = ?",
                        tuple(vals + [user_id]),
                    )
                )

        for rid in orig_ids - edited_ids:
            statements.append(
                (f"UPDATE {qname('Users')} SET Active = 0 WHERE UserId = ?", (rid,))
            )

        execute_many(statements)
        st.success("Users guardados.")
        st.rerun()


def render_admin_panel():
    """Renderiza el panel de admin embedible en app.py (sin set_page_config)."""
    st.subheader("Administrador de Datos Maestros")
    st.caption(f"Backend activo: {current_backend_label()}")

    try:
        _ = load_df("SELECT 1 AS ok")
    except Exception as exc:
        st.error(f"No se pudo conectar a la base: {exc}")
        return

    table = st.selectbox(
        "Tabla maestra",
        [
            "Plantas",
            "Divisiones",
            "Areas",
            "Categorias",
            "Subcategorias",
            "Prioridades",
            "Estados",
            "Users",
        ],
        key="admin_table_selector",
    )

    try:
        if table == "Plantas":
            df = load_df(
                f"SELECT PlantaId, Nombre, Activo FROM {qname('Plantas')} ORDER BY PlantaId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="admin_plantas"
            )
            if st.button("Guardar Plantas", use_container_width=True):
                save_simple_table(
                    df, edited, "Plantas", "PlantaId", ["Nombre", "Activo"], "Activo"
                )
                st.success("Plantas guardadas.")
                st.rerun()
        elif table == "Divisiones":
            df = load_df(
                f"SELECT DivisionId, Nombre, Activo FROM {qname('Divisiones')} ORDER BY DivisionId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="admin_divisiones"
            )
            if st.button("Guardar Divisiones", use_container_width=True):
                save_simple_table(
                    df,
                    edited,
                    "Divisiones",
                    "DivisionId",
                    ["Nombre", "Activo"],
                    "Activo",
                )
                st.success("Divisiones guardadas.")
                st.rerun()
        elif table == "Areas":
            area_editor()
        elif table == "Categorias":
            df = load_df(
                f"SELECT CategoriaId, Nombre, Activo FROM {qname('Categorias')} ORDER BY CategoriaId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="admin_categorias"
            )
            if st.button("Guardar Categorias", use_container_width=True):
                save_simple_table(
                    df,
                    edited,
                    "Categorias",
                    "CategoriaId",
                    ["Nombre", "Activo"],
                    "Activo",
                )
                st.success("Categorias guardadas.")
                st.rerun()
        elif table == "Subcategorias":
            subcategory_editor()
        elif table == "Prioridades":
            df = load_df(
                f"SELECT PrioridadId, Nombre, Nivel FROM {qname('Prioridades')} ORDER BY Nivel, PrioridadId"
            )
            edited = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key="admin_prioridades",
            )
            if st.button("Guardar Prioridades", use_container_width=True):
                save_simple_table(
                    df, edited, "Prioridades", "PrioridadId", ["Nombre", "Nivel"]
                )
                st.success("Prioridades guardadas.")
                st.rerun()
        elif table == "Estados":
            df = load_df(
                f"SELECT EstadoId, Nombre FROM {qname('Estados')} ORDER BY EstadoId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="admin_estados"
            )
            if st.button("Guardar Estados", use_container_width=True):
                save_simple_table(df, edited, "Estados", "EstadoId", ["Nombre"])
                st.success("Estados guardados.")
                st.rerun()
        elif table == "Users":
            user_editor()
    except Exception as exc:
        st.error(f"Error al guardar datos en {table}: {exc}")


def main():
    st.title("Administrador de Datos Maestros")
    st.caption(f"Backend activo: {current_backend_label()}")

    try:
        _ = load_df("SELECT 1 AS ok")
    except Exception as exc:
        st.error(f"No se pudo conectar a la base: {exc}")
        st.stop()

    table = st.selectbox(
        "Tabla maestra",
        [
            "Plantas",
            "Divisiones",
            "Areas",
            "Categorias",
            "Subcategorias",
            "Prioridades",
            "Estados",
            "Users",
        ],
    )

    try:
        if table == "Plantas":
            df = load_df(
                f"SELECT PlantaId, Nombre, Activo FROM {qname('Plantas')} ORDER BY PlantaId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="plantas"
            )
            if st.button("Guardar Plantas", use_container_width=True):
                save_simple_table(
                    df, edited, "Plantas", "PlantaId", ["Nombre", "Activo"], "Activo"
                )
                st.success("Plantas guardadas.")
                st.rerun()

        elif table == "Divisiones":
            df = load_df(
                f"SELECT DivisionId, Nombre, Activo FROM {qname('Divisiones')} ORDER BY DivisionId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="divisiones"
            )
            if st.button("Guardar Divisiones", use_container_width=True):
                save_simple_table(
                    df,
                    edited,
                    "Divisiones",
                    "DivisionId",
                    ["Nombre", "Activo"],
                    "Activo",
                )
                st.success("Divisiones guardadas.")
                st.rerun()

        elif table == "Areas":
            area_editor()

        elif table == "Categorias":
            df = load_df(
                f"SELECT CategoriaId, Nombre, Activo FROM {qname('Categorias')} ORDER BY CategoriaId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="categorias"
            )
            if st.button("Guardar Categorias", use_container_width=True):
                save_simple_table(
                    df,
                    edited,
                    "Categorias",
                    "CategoriaId",
                    ["Nombre", "Activo"],
                    "Activo",
                )
                st.success("Categorias guardadas.")
                st.rerun()

        elif table == "Subcategorias":
            subcategory_editor()

        elif table == "Prioridades":
            df = load_df(
                f"SELECT PrioridadId, Nombre, Nivel FROM {qname('Prioridades')} ORDER BY Nivel, PrioridadId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="prioridades"
            )
            if st.button("Guardar Prioridades", use_container_width=True):
                save_simple_table(
                    df, edited, "Prioridades", "PrioridadId", ["Nombre", "Nivel"]
                )
                st.success("Prioridades guardadas.")
                st.rerun()

        elif table == "Estados":
            df = load_df(
                f"SELECT EstadoId, Nombre FROM {qname('Estados')} ORDER BY EstadoId"
            )
            edited = st.data_editor(
                df, num_rows="dynamic", use_container_width=True, key="estados"
            )
            if st.button("Guardar Estados", use_container_width=True):
                save_simple_table(df, edited, "Estados", "EstadoId", ["Nombre"])
                st.success("Estados guardados.")
                st.rerun()

        elif table == "Users":
            user_editor()

    except Exception as exc:
        st.error(f"Error al guardar datos en {table}: {exc}")


if __name__ == "__main__":
    main()
