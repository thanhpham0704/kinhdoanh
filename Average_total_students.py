import streamlit as st
import requests
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import pickle
import streamlit_authenticator as stauth
import numpy as np
import ast
# %%
page_title = "Trung bình giảm giá toàn học viên"
page_icon = "💸"
layout = "wide"
st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)

# ----------------------------------------
names = ["Phạm Tấn Thành", "Phạm Minh Tâm", "Vận hành", "Kinh doanh"]
usernames = ["thanhpham", "tampham", "vietopvanhanh", 'vietopkinhdoanh']

# Load hashed password
file_path = Path(__file__).parent / 'hashed_pw.pkl'
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                    "sales_dashboard", "abcdef", cookie_expiry_days=1)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    authenticator.logout("logout", "main")

    # Add CSS styling to position the button on the top right corner of the page
    st.markdown(
        """
            <style>
            .stButton button {
                position: absolute;
                top: 0px;
                right: 0px;
            }
            </style>
            """,
        unsafe_allow_html=True
    )
    st.title(page_title + " " + page_icon)
    # ----------------------#
    # Filter
    now = datetime.now()
    DEFAULT_START_DATE = datetime(now.year, now.month, 1)
    DEFAULT_END_DATE = datetime(now.year, now.month, 1) + timedelta(days=32)
    DEFAULT_END_DATE = DEFAULT_END_DATE.replace(day=1) - timedelta(days=1)

    # Create a form to get the date range filters
    with st.sidebar.form(key='date_filter_form'):
        ketoan_start_time = st.date_input(
            "Select start date", value=DEFAULT_START_DATE)
        ketoan_end_time = st.date_input(
            "Select end date", value=DEFAULT_END_DATE)
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)

    @st.cache_data(ttl=timedelta(days=1))
    def collect_data(link):
        return (pd.DataFrame((requests.get(link).json())))

    @st.cache_data()
    def rename_lop(dataframe, column_name):
        dataframe[column_name] = dataframe[column_name].replace(
            {1: "Hoa Cúc", 2: "Gò Dầu", 3: "Lê Quang Định", 5: "Lê Hồng Phong"})
        return dataframe

    @st.cache_data()
    def grand_total(dataframe, column):
        # create a new row with the sum of each numerical column
        totals = dataframe.select_dtypes(include=[float, int]).sum()
        totals[column] = "Grand total"
        # append the new row to the dataframe
        dataframe = dataframe.append(totals, ignore_index=True)
        return dataframe
        # Define a function

    @st.cache_data()
    def grand_total_mean(dataframe, column):
        # create a new row with the sum of each numerical column
        totals = dataframe.select_dtypes(include=[float, int]).mean()
        totals[column] = "Grand total"
        # append the new row to the dataframe
        dataframe = dataframe.append(totals, ignore_index=True)
        return dataframe

    @st.cache_data(ttl=timedelta(days=1))
    def collect_filtered_data(table, date_column='', start_time='', end_time=''):
        link = f"https://vietop.tech/api/get_data/{table}?column={date_column}&date_start={start_time}&date_end={end_time}"
        df = pd.DataFrame((requests.get(link).json()))
        df[date_column] = pd.to_datetime(df[date_column])
        # Extract date portion from datetime values
        df[date_column] = df[date_column].dt.date
        return df

    @st.cache_data()
    def plotly_chart(df, yvalue, xvalue, text, title, y_title, x_title, color=None, discrete_sequence=None, map=None):
        fig = px.bar(df, y=yvalue,
                     x=xvalue, text=text, color=color, color_discrete_sequence=discrete_sequence, color_discrete_map=map)
        fig.update_layout(
            title=title,
            yaxis_title=y_title,
            xaxis_title=x_title,
        )
        fig.update_traces(textposition='auto')
        return fig
    @st.cache_data()
    def bar(df, yvalue, xvalue, text, title, y_title, x_title, color=None, discrete_sequence=None, map=None):
        fig = px.bar(df, y=yvalue,
                     x=xvalue, text=text, color=color, color_discrete_sequence=discrete_sequence, color_discrete_map=map)
        fig.update_layout(
            title=title,
            yaxis_title=y_title,
            xaxis_title=x_title)
        fig.update_layout(font=dict(size=17), xaxis={
            'categoryorder': 'total descending'})
        return fig
# %%
    # "---------------" Thông tin lương giáo viên

    khoahoc = collect_data('https://vietop.tech/api/get_data/khoahoc')
    khoahoc_me = khoahoc.query("kh_parent_id == 0 and kh_active == 1")
    lophoc = collect_data(
        'https://vietop.tech/api/get_data/lophoc').query("deleted_at.isnull()")
    discounts = collect_data('https://vietop.tech/api/get_data/discounts')
    molop = collect_data('https://vietop.tech/api/get_data/molop')
    hocvien = collect_data('https://vietop.tech/api/get_data/hocvien')
    users = collect_data('https://vietop.tech/api/get_data/users')
    order_details = collect_data('https://vietop.tech/api/get_data/order_details')#.loc[:, ['hv_id', 'detail_status']]
    
    # Filter date
    orders = collect_filtered_data(table='orders', date_column='created_at',
                                   start_time=ketoan_start_time, end_time=ketoan_end_time)
    
    khoahoc_me.drop_duplicates(subset='kh_id', inplace = True)
    # Create lophoc_khoahoc
    lophoc_khoahoc = lophoc.merge(
        khoahoc_me[['kh_id', 'kh_ten']], left_on='kh_parent', right_on='kh_id', validate='many_to_one')
    lophoc_khoahoc = lophoc_khoahoc[[
        'lop_id', 'kh_ten', 'class_type', 'class_status']]

    import ast
    discount_subset = discounts[[
        'dis_id', 'dis_name', 'is_percentage', 'is_discount_vnd']]
    order_discount = orders[['ketoan_id', 'hv_id', 'hv_discount', 'ketoan_coso', 'ketoan_active', 'kh_id', 'created_at']]\
        .merge(molop[['ketoan_id', 'lop_id']], on='ketoan_id', how='left')

    # Converting a string representation of a list into an actual list object
    def list_eval(x): return ast.literal_eval(x)
    order_discount['hv_discount'] = order_discount['hv_discount'].apply(
        list_eval)
    # Exploding the list
    order_discount = order_discount.explode('hv_discount')
    order_discount['hv_discount'] = order_discount['hv_discount'].astype(
        'int64')
    # Mapping ketoan_coso
    order_discount = rename_lop(order_discount, 'ketoan_coso')
    print(f"orders row {order_discount.shape}")
    # Merge discount_subset
    df = order_discount.merge(discount_subset, left_on='hv_discount',
                              right_on='dis_id', validate='many_to_one', how='left')  # left
    print(f"order merge discount {df.shape}")
    # Merge lophoc_khoahoc
    df = df.merge(lophoc_khoahoc, on='lop_id', how='left')  # left
    print(f"order and discount merge lophoc {df.shape}")
    # Mapping ketoan_active
    conditions = [(df['ketoan_active'] == 0), df['ketoan_active']
                  == 1, df['ketoan_active'] == 4, df['ketoan_active'] == 5]
    choices = ["Chưa học", "Đang học", "Bảo lưu", "Kết thúc"]
    df['ketoan_active'] = np.select(conditions, choices)
    # Fillna with ketoan_active
    df['kh_ten'] = df['kh_ten'].fillna(df['ketoan_active'])
    df['class_type'] = df['class_type'].fillna(df['ketoan_active'])
    df['class_status'] = df['class_status'].fillna(df['ketoan_active'])
    # Merge hocvien
    df = df.merge(
        hocvien[['hv_id', 'hv_fullname', 'user_id']], on='hv_id')  # inner
    # Merge users
    df = df.merge(users[['id', 'fullname']], left_on='user_id', right_on='id')
    # Filter khong khuyen mai
    df = df.query("dis_id != 0")
    # Drop unused columns
    df.drop(['id', 'dis_id', 'hv_discount', 'kh_id'], axis=1, inplace=True)
    details_discount = df.copy()
    details_discount = details_discount.rename(
        columns={'is_percentage': 'phần trăm khuyến mãi', 'is_discount_vnd': 'số tiền khuyến mãi', 'hv_fullname': 'tên học viên', 'fullname': 'tên EC'})
    # ---------------------
    # %%
    df2 = lophoc.merge(
        khoahoc_me[['kh_id', 'kh_ten']], left_on='kh_parent', right_on='kh_id')
    df2 = df2[[
        'lop_id', 'kh_ten', 'class_type', 'class_status', 'kh_parent']]
    df2 = df2.drop_duplicates(subset='kh_parent')
    # Merge
    orders_subset = orders[['hv_id', 'ketoan_id',
                            'ketoan_coso', 'ketoan_active', 'created_at', 'kh_id']]
    df3 = orders_subset.merge(df2, left_on='kh_id',
                              right_on='kh_parent', how='left')
    df4 = df3.merge(hocvien[['hv_id', 'hv_fullname', 'user_id']])\
        .merge(users[['fullname', 'id']], left_on='user_id', right_on='id')
    df4 = df4.drop(['kh_id', 'kh_parent', 'id'], axis=1)
    df4['dis_name'] = 'không khuyến mãi'
    df4['is_percentage'] = 0
    df4['is_discount_vnd'] = 0
    df4 = rename_lop(df4, 'ketoan_coso')
    # Mapping ketoan_active
    conditions = [(df4['ketoan_active'] == 0), df4['ketoan_active']
                  == 1, df4['ketoan_active'] == 4, df4['ketoan_active'] == 5]
    choices = ["Chưa học", "Đang học", "Bảo lưu", "Kết thúc"]
    df4['ketoan_active'] = np.select(conditions, choices)
    # Fillna with ketoan_active
    df4['kh_ten'] = df4['kh_ten'].fillna(df4['ketoan_active'])
    df4['class_type'] = df4['class_type'].fillna(df4['ketoan_active'])
    df4['class_status'] = df4['class_status'].fillna(df4['ketoan_active'])
    # Concat discount and non-discount
    df5 = pd.concat([df, df4], axis=0)
    # Create kh_ten_group from kh_ten
    df5['kh_ten_group'] = [
        'Lớp Kèm' if "Kèm" in i else 'Lớp Nhóm' if 'Nhóm' in i else i for i in df5['kh_ten']]
    # Create a form to filter coso
    with st.sidebar.form(key='coso_filter_form'):
        coso_filter = st.multiselect(label="Select cơ sở:",
                                     options=list(df5['ketoan_coso'].unique()), default=['Hoa Cúc', 'Gò Dầu', 'Lê Hồng Phong', 'Lê Quang Định'])
        submit_button = st.form_submit_button(
            label='Filter',  use_container_width=True)
    df5 = df5[df5['ketoan_coso'].isin(coso_filter)]
    
    
    # df5 = df5.query("class_status != 'complete'")
    # %%
    # Only get students who enrol for the first time in the course (detail_status == 1)
    hv_dong_khoa_moi_list = order_details.query("detail_status == 1")['hv_id'].to_list()
    df5 = df5[df5['hv_id'].isin(hv_dong_khoa_moi_list)]
    # Filter lophoc
    df5 = df5.merge(lophoc[['lop_id', 'lop_end', 'class_status']], on = 'lop_id', how = 'left', validate= 'many_to_one')
    
    df5['lop_end'] = df5['lop_end'].astype("datetime64[ns]").dt.date
    
    df5 = df5[(df5['class_status_x'].isin(['progress', 'Chưa học'])) | \
              ((df5['class_status_x'] == 'complete') & (df5['lop_end'] <= ketoan_end_time) & (df5['lop_end'] >= ketoan_start_time))]

    # Percentage total
    df_percentage = df5.query("is_discount_vnd == 0")
    # Amount total
    df_amount = df5.query("is_percentage == 0")
    # %%

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.warning("(1) Tổng PĐK:")
        st.subheader(df5.shape[0])
    with col2:
        st.warning("(2) Tổng PĐK giảm giá %:")
        st.subheader(df5.query("is_percentage != 0").shape[0])
    with col3:
        st.warning("(3) Tổng PĐK giảm giá số tiền:")
        st.subheader(df5.query("is_discount_vnd != 0").shape[0])
    with col4:
        st.warning("(4) Tổng PĐK không giảm giá:")
        st.subheader(
            df5.query("is_percentage == 0 and is_discount_vnd == 0").shape[0])
    st.markdown("---")

    # ---------------------
    # Percentage
    # df_percentage = df.query("is_percentage != 0")
    # Percentage groupby ketoan_coso
    col1, col2 = st.columns(2)
    with col1:
        st.warning("Trung bình giảm giá % toàn Vietop")
        st.subheader(f"{round(df_percentage.is_percentage.mean(), 2)/100:.2%}")

    with col2:
        st.warning("Trung bình giảm giá số tiền toàn Vietop")
        st.subheader(f"{round(df_amount.is_discount_vnd.mean(), 2):,} VND")
    df_percentage_group = df_percentage.groupby("ketoan_coso", as_index=False)[
        'is_percentage'].agg(['mean', 'count']).reset_index()
    st.markdown("---")
    df_percentage_group['mean'] = round(df_percentage_group['mean'], 2)

    ""
    

    # st.subheader("Trung bình phần trăm giảm giá theo chi nhánh")
    # st.dataframe(df_percentage_group.set_index(
    #     "ketoan_coso"))
    df_percentage_1 = df_percentage_group.copy()
    # Create fig1 -------------------------------------
    fig1 = bar(df_percentage_group, yvalue='mean',
               xvalue='ketoan_coso', text=df_percentage_group["mean"].apply(
                   lambda x: '{:.2%}'.format(x/100)), title='Trung bình phần trăm giảm giá', x_title='Chi nhánh', y_title='Trung bình', color='ketoan_coso', map={
                   'Hoa Cúc': '#ffc107',
                   'Gò Dầu': '#07a203',
                   'Lê Quang Định': '#2196f3',
                   'Lê Hồng Phong': '#e700aa',
                   'Grand total': 'white'})
    fig1.update_traces(
        hovertemplate="% Giảm giá: %{y:,.0f}<extra></extra>")
    # st.plotly_chart(fig1, use_container_width=True)
    # Create fig1_end -------------------------------------
    # Percentage groupby class_type
    df_percentage_group = df_percentage.groupby("class_type", as_index=False)[
        'is_percentage'].agg(['mean', 'count']).reset_index()
    # st.subheader("Trung bình phần trăm giảm giá theo on/off")
    # st.dataframe(df_percentage_group)
    df_percentage_2 = df_percentage_group.copy()

    # Create fig2 -------------------------------------
    fig2 = bar(df_percentage_group, yvalue='mean',
               xvalue='class_type', text=df_percentage_group["mean"].apply(
                   lambda x: '{:.2%}'.format(x/100)), title='Trung bình phần trăm giảm giá', x_title='Online / Offline', y_title='Trung bình',)
    fig2.update_traces(
        hovertemplate="% Giảm giá: %{y:,.0f}<extra></extra>")
    # st.plotly_chart(fig2, use_container_width=True)
    # Create fig2_end -------------------------------------
    # Percentage groupby kh_ten
    df_percentage_group = df_percentage.groupby("kh_ten_group", as_index=False)[
        'is_percentage'].agg(['mean', 'count']).reset_index()
    # st.subheader("Trung bình phần trăm giảm giá theo kh_ten")
    # st.dataframe(df_percentage_group)
    df_percentage_3 = df_percentage_group.copy()

    # Create fig3 -------------------------------------
    fig3 = bar(df_percentage_group, yvalue='mean',
               xvalue='kh_ten_group', text=df_percentage_group["mean"].apply(
                   lambda x: '{:.2%}'.format(x/100)), title='Trung bình phần trăm giảm giá', x_title='Khoá học', y_title='Trung bình',)
    fig3.update_traces(
        hovertemplate="% Giảm giá: %{y:,.0f}<extra></extra>")
    # st.plotly_chart(fig3, use_container_width=True)
    # Create fig3_end -------------------------------------
    # Percentage groupby EC
    df_percentage_group = df_percentage.groupby(["fullname", "user_id"], as_index=False)[
        'is_percentage'].agg(['mean', 'count']).reset_index()
    # st.subheader("Trung bình phần trăm giảm giá theo EC")
    # st.dataframe(df_percentage_group)
    df_percentage_4 = df_percentage_group.copy()
    # Create fig4 -------------------------------------
    fig4 = bar(df_percentage_group.query("mean != 0"), yvalue='mean',
               xvalue='fullname', text=df_percentage_group.query("mean != 0")["mean"].apply(
                   lambda x: '{:.2%}'.format(x/100)), title='Trung bình phần trăm giảm giá', x_title='Tên EC', y_title='Trung bình',)
    fig4.update_traces(
        hovertemplate="% Giảm giá: %{y:,.0f}<extra></extra>")
    # st.plotly_chart(fig4, use_container_width=True)
    # Create fig4_end -------------------------------------
    # Amount
    # df_amount = df.query("is_discount_vnd != 0")
    # Amount groupby ketoan_coso
    df_amount_group = df_amount.groupby("ketoan_coso", as_index=False)[
        'is_discount_vnd'].agg(['mean', 'count']).reset_index()
    df_amount_group['mean'] = round(df_amount_group['mean'], 2)
    # st.subheader("Trung bình số tiền giảm giá theo chi nhánh")
    # st.dataframe(df_amount_group)
    df_percentage_5 = df_amount_group.copy()
    # Create fig5 -------------------------------------
    fig5 = bar(df_amount_group, yvalue='mean',
               xvalue='ketoan_coso', text=df_amount_group["mean"], title='Trung bình số tiền giảm giá', x_title='Chi nhánh', y_title='Trung bình', color='ketoan_coso', map={
                   'Hoa Cúc': '#ffc107',
                   'Gò Dầu': '#07a203',
                   'Lê Quang Định': '#2196f3',
                   'Lê Hồng Phong': '#e700aa',
                   'Grand total': 'white'})
    fig5.update_traces(
        # Add the thousand divider to the text
        hovertemplate="Trung bình số tiền giảm giá: %{y:,.0f}<extra></extra>", texttemplate='%{text:,.0f}',
        textposition='auto')

    # st.plotly_chart(fig5, use_container_width=True)
    # Create fig5_end -------------------------------------

    # Amount groupby class_type
    df_amount_group = df_amount.groupby("class_type", as_index=False)[
        'is_discount_vnd'].agg(['mean',  'count']).reset_index()
    # st.subheader("Trung bình số tiền giảm giá theo on/off")
    # st.dataframe(df_amount_group)
    df_percentage_6 = df_amount_group.copy()
    # Create fig6 -------------------------------------
    fig6 = bar(df_amount_group, yvalue='mean',
               xvalue='class_type', text=df_amount_group["mean"], title='Trung bình số tiền giảm giá', x_title='Online / Offline', y_title='Trung bình',)
    fig6.update_traces(
        # Add the thousand divider to the text
        hovertemplate="Trung bình số tiền giảm giá: %{y:,.0f}<extra></extra>", texttemplate='%{text:,.0f}',
        textposition='auto')

    # st.plotly_chart(fig6, use_container_width=True)
    # Create fig6_end -------------------------------------
    # Amount groupby kh_ten
    df_amount_group = df_amount.groupby("kh_ten_group", as_index=False)[
        'is_discount_vnd'].agg(['mean', 'count']).reset_index()
    # st.subheader("Trung bình số tiền giảm giá theo kh_ten")
    # st.dataframe(df_amount_group)
    df_percentage_7 = df_amount_group.copy()
    # Create fig7 -------------------------------------
    fig7 = bar(df_amount_group, yvalue='mean',
               xvalue='kh_ten_group', text=df_amount_group["mean"], title='Trung bình số tiền giảm giá', x_title='Khoá học', y_title='Trung bình',)
    fig7.update_traces(
        # Add the thousand divider to the text
        hovertemplate="Trung bình số tiền giảm giá: %{y:,.0f}<extra></extra>", texttemplate='%{text:,.0f}',
        textposition='auto')
    # st.plotly_chart(fig7, use_container_width=True)
    # Create fig7_end -------------------------------------
    # Amount groupby EC
    df_amount_group = df_amount.groupby(["fullname", "user_id"], as_index=False)[
        'is_discount_vnd'].agg(['mean',  'count']).reset_index()
    # st.subheader("Trung bình phần trăm giảm giá theo EC")
    # st.dataframe(df_amount_group)
    df_percentage_8 = df_amount_group.copy()
    # Create fig8 -------------------------------------
    fig8 = bar(df_amount_group.query("mean !=0"), yvalue='mean',
               xvalue='fullname', text=df_amount_group.query("mean !=0")["mean"], title='Trung bình số tiền giảm giá', x_title='Tên EC', y_title='Trung bình',)
    fig8.update_traces(
        # Add the thousand divider to the text
        hovertemplate="Trung bình số tiền giảm giá: %{y:,.0f}<extra></extra>", texttemplate='%{text:,.0f}',
        textposition='auto')
    # st.plotly_chart(fig8, use_container_width=True)
    # Create fig8_end -------------------------------------

    def formating(df, col1, col3,):
        df = df.set_index(df.columns[0])
        df = df.style.background_gradient(cmap='PuBu')
        df = df.format({col1: '{:.2f}%',
                        col3: '{:,.0f}'})
        return df
    st.subheader("Trung bình giảm giá theo chi nhánh")
    df = df_percentage_1.merge(df_percentage_5, on='ketoan_coso', suffixes=[
        '_%', '_sotien'], how = 'outer')
    df = formating(df, 'mean_%',  'mean_sotien')
    st.dataframe(df)

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig1, use_container_width=True)
    col2.plotly_chart(fig5, use_container_width=True)
    "---"
    st.subheader("Trung bình giảm giá theo online/offline")
    df = df_percentage_2.merge(df_percentage_6, on='class_type', suffixes=[
        '_%', '_sotien'], how = 'outer')
    df = formating(df, 'mean_%',  'mean_sotien')
    st.dataframe(df)
    col1, col2 = st.columns(2)
    col1.plotly_chart(fig2, use_container_width=True)
    col2.plotly_chart(fig6, use_container_width=True)
    "---"
    st.subheader("Trung bình giảm giá theo khoá học")
    df = df_percentage_3.merge(df_percentage_7, on='kh_ten_group', suffixes=[
        '_%', '_sotien'], how = 'outer')
    df = formating(df, 'mean_%',  'mean_sotien')
    st.dataframe(df)

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig3, use_container_width=True)
    col2.plotly_chart(fig7, use_container_width=True)
    "---"
    st.subheader("Trung bình giảm giá theo EC")
    df = df_percentage_4.merge(df_percentage_8, on=['user_id', 'fullname'], suffixes=[
        '_%', '_sotien'], how = 'outer').drop(
        'user_id', axis=1)
    df = formating(df, 'mean_%', 'mean_sotien')
    st.dataframe(df)

    st.plotly_chart(fig4, use_container_width=True)
    st.plotly_chart(fig8, use_container_width=True)
    "---"
    st.subheader("Chi tiết giảm giá")
    df5 = df5.drop("user_id", axis=1)
    df5 = df5.rename(
        columns={'is_percentage': 'phần trăm khuyến mãi', 'is_discount_vnd': 'số tiền khuyến mãi', 'hv_fullname': 'tên học viên', 'fullname': 'tên EC'})
    st.warning(
        f"Tổng PĐK mới trong tháng {ketoan_start_time.month} là: {df5.shape[0]}")
    st.warning(
        f"Bao gồm học viên mới hoàn toàn + học viên cũ nhưng đóng tiền khoá mới)")
    st.dataframe(df5.set_index("hv_id"), use_container_width=True)
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        df5.to_excel(writer, sheet_name='Sheet1')
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        st.download_button(
            label="Download chi tiết giảm giá worksheets",
            data=buffer,
            file_name="giamgia_details.xlsx",
            mime="application/vnd.ms-excel"
        )
