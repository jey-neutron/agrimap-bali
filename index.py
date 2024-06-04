import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import sys
from pathlib import Path
import datetime

try:
    # MAIN VIEW ============================
    # header html
    st.set_page_config(page_title="Agrimap Bali", layout="wide", page_icon="🗺️")
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
        """, 
        unsafe_allow_html=True
    )

    col = st.columns([1,2])
    with col[0]:
        st.title("Dashboard Agrimap Bali")
    with col[1]:
        st.write("Dashboard ini bertujuan untuk memetakan luas tanam atau panen padi berdasarkan hasil machine learning dan citra satelit.")
        st.write("Peta heatmap di bawah akan menampilkan jenis fase tanaman padi yang terpilih. Terdapat juga data pendukung atau rekomendasi di bawah untuk melihat lebih detail potensi wilayah tersebut.")

    # load file path
    this_path = Path().resolve()
    kec_path = str(this_path) + r"/map_source/geo_kec.geojson"
    
    # load in geopandas using function to improv performance
    @st.cache_data
    def read_gpd(path):
        return gpd.read_file(path, driver='GeoJSON')
    
    #kec_gdf = gpd.read_file(kec_path, driver='GeoJSON')
    kec_gdf = read_gpd(kec_path)
    #kec_gdf = kec_gdf.to_crs("WGS84")

    # kab and its centroid
    kdkab = {'-':'-',
            '01': ["JEMBRANA",-8.3606,114.6257], 
            '02': ["TABANAN",-8.5376,115.1247], 
            '03': ["BADUNG",-8.5819,115.1771],
            '04': ["GIANYAR",-8.5367,115.3314],
            '05': ["KLUNGKUNG",-8.5388,115.4024],
            '06': ["BANGLI",-8.4543,115.3549],
            '07': ["KARANGASEM",-8.4463,115.6127],
            '08': ["BULELENG",-8.2239,114.9517],
            '71': ["DENPASAR",-8.6705,115.2126]
        }
    def get_nmkab(kode): #from dict above
        return kdkab[kode][0]
    def get_latlonkab(kode): #return lat,lon
        return kdkab[kode][1], kdkab[kode][2]
    
    
    # SIDEBAR VIEW ============================
    with st.sidebar: #.form(key="my_form"):
        st.header("Filter Data")
        
        # PILIH kab
        selectbox_kab = st.selectbox("Pilih Kabupaten", options=list(kdkab.keys()), format_func=get_nmkab)
        # set pilihan kec based on pilihan kab
        kec_choices = ["KUTA SELATAN"]#list( set(
                #kec_gdf.loc[kec_gdf['nmkab'] == get_nmkab(selectbox_kab)].nmkec
            #) )
        kec_choices.insert(0, "-")
        des_path = str(this_path) + f"/map_source/geo_desa_{selectbox_kab}.geojson"
        
        # PILIH kec
        judulkec = " di KAB. "+get_nmkab(selectbox_kab) if selectbox_kab != '-' else ""
        selectbox_kec = st.selectbox("Pilih Kecamatan"+judulkec, kec_choices)

        # PILIH display choropleth
        #st.write('<style>div.row-widget.stRadio > div{flex-direction:row;justify-content: center;} </style>', unsafe_allow_html=True)
        #t.write('<style>div.st-bf{flex-direction:column;} div.st-ag{font-weight:bold;padding-left:2px;}</style>', unsafe_allow_html=True)
        opt_displaymap = ["Vegetatif 1","Vegetatif 2","Generatif","Persiapan Lahan"]
        choose_displaymap=st.radio("Display map: ",opt_displaymap, index=2) #pilihan defaultnya Generatif

        # PILIH date file source
        from os import walk
        csv_path = str(this_path) + r"/data"
        csv_list = [[],[]]
        for (dirpath, dirnames, filenames) in walk(csv_path, topdown=False):
            for filename in filenames:
                csv_list[0].append(filename.split('_')[0])
                csv_list[1].append(filename.split('_')[1].split('.')[0])
            break
        
        kdbln = {
            #'01':'Januari',
            #'02':'Februari',
            #'03':'Maret',
            #'04':'April',
            #'05':'Mei',
            #'06':'Juni',
            #'07':'Juli',
            #'08':'Agustus',
            '09':'September',
            #'10':'Oktober',
            #'11':'November',
            #'12':'Desember'
        }
        def get_namabln(kode):
            return kdbln[kode]
        
        col1, col2 = st.columns(2)
        with col1:
            datenow = datetime.datetime.now()
            selectbox_bln = st.selectbox("Bulan:", options=list(kdbln.keys()), format_func=get_namabln, 
                                         #index=datenow.date().month-1) #dummy only
                                         index=0)
        with col2:
            selectbox_thn = st.selectbox("Tahun:", set(csv_list[1]), index=len(set(csv_list[1]))-1 )

    #    pressed_filter = st.form_submit_button("Filter Map")
    # if submit form filter
    #if pressed_filter:
    #    kec_gdf = kec_gdf[kec_gdf["nmkab"] == selectbox_kab]

    # DATA FOR MAPPING
    titiktengah = False
    if Path(des_path).exists() :
        # koordinat centroid zoom map kec
        if selectbox_kec != '-':
            titiktengah = kec_gdf[kec_gdf['nmkec'] == selectbox_kec ].geometry.centroid.iloc[0]
        
        # read desa di kec terpilih
        #des_gdf = gpd.read_file(des_path, driver='GeoJSON')
        des_gdf = read_gpd(des_path)
        if selectbox_kec != '-':
            des_gdf = des_gdf.loc[des_gdf['nmkec'] == selectbox_kec ]
        des_gdf['nmkab'] = get_nmkab(selectbox_kab)
        #st.write(des_gdf.iddesa)
        
        # filter display map and date
        des_df = pd.read_csv(csv_path+f"/{selectbox_bln}_{selectbox_thn}.csv", dtype={'iddesa': object})
        #des_dfmap = des_df.iloc[:,[0,opt_displaymap.index(choose_displaymap)+1]]
        #st.write("Column choosen: ", des_df.columns)
        des_df = des_gdf.merge(des_df, how='inner', on='iddesa')
        des_df['total'] = des_df['vegetatif1'] + des_df['vegetatif2'] + des_df['generatif'] + des_df['persiapan'] + des_df['nonsawah']
        
        # data final for display map
        #kec_gdf = kec_gdf.drop('nmdesa', axis=1)
        #kec_gdf = kec_gdf.merge(des_gdf, how='outer')
        kec_gdf = des_df

    # MAIN VIEW MAPPING ============================
    hover_data = [kec_gdf.nmkec, kec_gdf.nmdesa, kec_gdf.generatif, kec_gdf.vegetatif1, kec_gdf.vegetatif2, kec_gdf.persiapan] if selectbox_kab != '-' else [kec_gdf.nmkec]
    figmap = px.choropleth_mapbox(
                        kec_gdf,
                        geojson=kec_gdf.geometry,
                        locations=kec_gdf.index,
                        color="luas" if selectbox_kab=='-' else des_df.columns[opt_displaymap.index(choose_displaymap)+8],
                        color_continuous_scale=px.colors.sequential.Sunsetdark,
                        hover_name=kec_gdf.nmkab,
                        hover_data= hover_data
                        #color_continuous_scale="Viridis",
                    )
    # set layout map
    figmap.update_layout(
        mapbox_zoom=8,
        mapbox_center= {"lat": -8.409518, "lon": 115.188919}, 
        margin={"r":0,"t":0,"l":0,"b":0},
        #mapbox_style='carto-positron',
        mapbox_style='open-street-map',
    )
    # layout map jika filter kab
    if selectbox_kab != "-":
        figmap.update_layout(
            mapbox_zoom=9,
            mapbox_center={"lat": get_latlonkab(selectbox_kab)[0], 
                           "lon":get_latlonkab(selectbox_kab)[1]}
        )
    # layout map jika filter kec
    if titiktengah:
        figmap.update_layout(
            mapbox_zoom=10,
            mapbox_center={"lat": titiktengah.y, "lon": titiktengah.x}
        )

    # show in web
    st.write(" ")
    st.plotly_chart(figmap)

    # SEE DF DETAILS
    if selectbox_kab !="-":
        # gtw gapenting
        st.markdown(
            """
            <style>
                .fixedButton{
                    position: fixed;
                    bottom: 0px;
                    right: 0px; 
                    padding: 20px;
                }
                .roundedFixedBtn{
                    height: 60px;
                    line-height: 60px;  
                    width: 60px;  
                    font-size: 2em;
                    font-weight: bold;
                    border-radius: 50%;
                    background-color: #0094de;
                    color: white;
                    text-align: center;
                    cursor: pointer;
                }
            </style>
            <hr>
            <div class="fixedButton" onclick="bottomFunction()" title="Scroll down">
                <div class="roundedFixedBtn"><i class="fa fa-arrow-circle-down"></i></div>
            </div>
            <script>
                function bottomFunction() {
                    document.getElementById('bottom').scrollIntoView({behavior: "smooth"});
                }
            </script>
            """, unsafe_allow_html=True
        )        

        col3, col4 = st.columns([3,1])
        with col3: 
            #st.write("df des col:", des_df.columns)
            dfstack = des_df.iloc[:,[3,8,9,10,11]].set_index("nmdesa").stack().to_frame().reset_index()
            dfstack.columns = ['Nama desa','Kategori','Persentase']
            figbar = px.bar(
                dfstack,
                y="Nama desa",
                x='Persentase',
                color='Kategori',
                color_discrete_sequence=px.colors.qualitative.Plotly_r
            )
            st.plotly_chart(figbar)
        
        with col4:
            st.subheader("Rekomendasi / Data pendukung")
            if selectbox_kec == '-':
                st.caption("KAB. "+str(selectbox_kab))
            else:
                st.caption("KEC. "+str(selectbox_kec))
            st.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed felis arcu, mollis sit amet orci nec, tincidunt eleifend tortor. In vehicula est eget enim eleifend, ac aliquam sem gravida. Suspendisse arcu lectus, ornare viverra mi eu, egestas placerat lectus.")

    #getrowindex = st.number_input('Enter an index of row to show')
    #st.write(kec_gdf.iloc[int(getrowindex)])
    st.markdown("<div id='bottom'>  </div>", unsafe_allow_html=True)


except Exception as e:
    #st.write("Terjadi error: ", str(e))
    exc_type, exc_obj, exc_tb = sys.exc_info()
    print(exc_type, exc_tb.tb_lineno)
    st.error(
        f"""
        **Terjadi kesalahan.**
        Error: {e}. Type error: {exc_type}, on line no {exc_tb.tb_lineno}
    """
    )
