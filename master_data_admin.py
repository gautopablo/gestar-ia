import os

import pandas as pd
import pyodbc
import streamlit as st


st.set_page_config(page_title="Gestar Admin Maestros", layout="wide")


def get_secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)


def get_connection():
    conn_str = get_secret("ODBC_CONN_STR")
    if not conn_str:
        raise RuntimeError("Falta ODBC_CONN_STR en secrets o variables de entorno.")
    return pyodbc.connect(conn_str)


SCHEMA = get_secret("DB_SCHEMA", "gestar")


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


def save_simple_table(df_original, df_edited, table, id_col, data_cols, soft_delete_col=None):
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
                (f"INSERT INTO {SCHEMA}.{table} ({cols_sql}) VALUES ({qmarks})", tuple(values))
            )
        else:
            rid_int = int(rid)
            edited_ids.add(rid_int)
            set_sql = ", ".join([f"{c} = ?" for c in data_cols])
            updates.append(
                (
                    f"UPDATE {SCHEMA}.{table} SET {set_sql} WHERE {id_col} = ?",
                    tuple(values + [rid_int]),
                )
            )

    if soft_delete_col:
        removed_ids = orig_ids - edited_ids
        for rid in removed_ids:
            updates.append(
                (
                    f"UPDATE {SCHEMA}.{table} SET {soft_delete_col} = 0 WHERE {id_col} = ?",
                    (rid,),
                )
            )

    execute_many(updates)


def area_editor():
    divisions = load_df(f"SELECT DivisionId, Nombre FROM {SCHEMA}.Divisiones ORDER BY Nombre")
    div_map = {r["Nombre"]: int(r["DivisionId"]) for _, r in divisions.iterrows()}
    div_names = list(div_map.keys())

    df = load_df(
        f"""
        SELECT a.AreaId, a.Nombre, a.DivisionId, d.Nombre AS Division, a.Activo
        FROM {SCHEMA}.Areas a
        LEFT JOIN {SCHEMA}.Divisiones d ON d.DivisionId = a.DivisionId
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
                        f"INSERT INTO {SCHEMA}.Areas (Nombre, DivisionId, Activo) VALUES (?, ?, ?)",
                        (nombre, div_id, int(activo)),
                    )
                )
            else:
                area_id = int(area_id)
                edited_ids.add(area_id)
                div_id = div_map.get(division_name) if division_name else None
                statements.append(
                    (
                        f"UPDATE {SCHEMA}.Areas SET Nombre = ?, DivisionId = ?, Activo = ? WHERE AreaId = ?",
                        (nombre, div_id, int(activo), area_id),
                    )
                )

        for rid in (orig_ids - edited_ids):
            statements.append((f"UPDATE {SCHEMA}.Areas SET Activo = 0 WHERE AreaId = ?", (rid,)))
        execute_many(statements)
        st.success("Areas guardadas.")
        st.rerun()


def subcategory_editor():
    categorias = load_df(
        f"SELECT CategoriaId, Nombre FROM {SCHEMA}.Categorias ORDER BY Nombre"
    )
    cat_map = {r["Nombre"]: int(r["CategoriaId"]) for _, r in categorias.iterrows()}
    cat_names = list(cat_map.keys())

    df = load_df(
        f"""
        SELECT s.SubcategoriaId, s.Nombre, s.CategoriaId, c.Nombre AS Categoria, s.Activo
        FROM {SCHEMA}.Subcategorias s
        JOIN {SCHEMA}.Categorias c ON c.CategoriaId = s.CategoriaId
        ORDER BY s.SubcategoriaId
        """
    )
    view = df[["SubcategoriaId", "Nombre", "Categoria", "Activo"]].copy()
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=cat_names),
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
                        f"INSERT INTO {SCHEMA}.Subcategorias (Nombre, CategoriaId, Activo) VALUES (?, ?, ?)",
                        (nombre, cat_id, int(activo)),
                    )
                )
            else:
                sub_id = int(sub_id)
                edited_ids.add(sub_id)
                cat_id = cat_map.get(categoria_name) if categoria_name else None
                statements.append(
                    (
                        f"UPDATE {SCHEMA}.Subcategorias SET Nombre = ?, CategoriaId = ?, Activo = ? WHERE SubcategoriaId = ?",
                        (nombre, cat_id, int(activo), sub_id),
                    )
                )

        for rid in (orig_ids - edited_ids):
            statements.append(
                (f"UPDATE {SCHEMA}.Subcategorias SET Activo = 0 WHERE SubcategoriaId = ?", (rid,))
            )
        execute_many(statements)
        st.success("Subcategorias guardadas.")
        st.rerun()


def main():
    st.title("Administrador de Datos Maestros (Azure)")
    st.caption(f"Esquema activo: {SCHEMA}")

    try:
        _ = load_df("SELECT 1 AS ok")
    except Exception as exc:
        st.error(f"No se pudo conectar a la base Azure: {exc}")
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
            df = load_df(f"SELECT PlantaId, Nombre, Activo FROM {SCHEMA}.Plantas ORDER BY PlantaId")
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="plantas")
            if st.button("Guardar Plantas", use_container_width=True):
                save_simple_table(df, edited, "Plantas", "PlantaId", ["Nombre", "Activo"], "Activo")
                st.success("Plantas guardadas.")
                st.rerun()

        elif table == "Divisiones":
            df = load_df(
                f"SELECT DivisionId, Nombre, Activo FROM {SCHEMA}.Divisiones ORDER BY DivisionId"
            )
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="divisiones")
            if st.button("Guardar Divisiones", use_container_width=True):
                save_simple_table(
                    df, edited, "Divisiones", "DivisionId", ["Nombre", "Activo"], "Activo"
                )
                st.success("Divisiones guardadas.")
                st.rerun()

        elif table == "Areas":
            area_editor()

        elif table == "Categorias":
            df = load_df(
                f"SELECT CategoriaId, Nombre, Activo FROM {SCHEMA}.Categorias ORDER BY CategoriaId"
            )
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="categorias")
            if st.button("Guardar Categorias", use_container_width=True):
                save_simple_table(
                    df, edited, "Categorias", "CategoriaId", ["Nombre", "Activo"], "Activo"
                )
                st.success("Categorias guardadas.")
                st.rerun()

        elif table == "Subcategorias":
            subcategory_editor()

        elif table == "Prioridades":
            df = load_df(
                f"SELECT PrioridadId, Nombre, Nivel FROM {SCHEMA}.Prioridades ORDER BY Nivel, PrioridadId"
            )
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="prioridades")
            if st.button("Guardar Prioridades", use_container_width=True):
                save_simple_table(df, edited, "Prioridades", "PrioridadId", ["Nombre", "Nivel"])
                st.success("Prioridades guardadas.")
                st.rerun()

        elif table == "Estados":
            df = load_df(f"SELECT EstadoId, Nombre FROM {SCHEMA}.Estados ORDER BY EstadoId")
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="estados")
            if st.button("Guardar Estados", use_container_width=True):
                save_simple_table(df, edited, "Estados", "EstadoId", ["Nombre"])
                st.success("Estados guardados.")
                st.rerun()

        elif table == "Users":
            df = load_df(
                f"SELECT UserId, Username, Email, Role, Active FROM {SCHEMA}.Users ORDER BY UserId"
            )
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="users")
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

    except Exception as exc:
        st.error(f"Error al guardar datos en {table}: {exc}")


if __name__ == "__main__":
    main()
