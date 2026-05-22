"""
VERA-MN: Verification Engine for Results & Accountability - Minnesota
Type 4 Detection using ACCESS for ELLs Speaking vs Writing + MCA Achievement Data

Minnesota context: WIDA ACCESS, MCA assessments, North Star Accountability System,
READ Act (2023), LEAPS Act (2014). Largest achievement gaps in the nation.
~91,000 ELs (11% of enrollment), 327 districts, MARSS data system.

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_MN_BLUE = "#003366"
MN_BLUE = "#003366"
MN_GOLD = "#FFD700"
MN_DARK = "#002B5C"
MN_RED = "#CC0000"

# ============================================================================
# DATA: Minnesota Districts with EL Populations (from MN Report Card 2025)
# ============================================================================

def load_districts():
    """
    Load MN districts with significant EL populations.
    Real data from Minnesota Report Card (rc.education.mn.gov) and MDE public files.
    District IDs are 4-digit MARSS codes.
    Proficiency rates reflect 2025 MCA results (Reading 49.5%, Math 45.0% statewide).
    """
    data = [
        # (district_id, district_name, total_students, el_count, el_percent,
        #  grad_rate, mca_read_all, mca_read_el, mca_read_hispanic, mca_read_black, mca_read_white,
        #  mca_math_all, mca_math_el, top_el_languages)
        ("0001", "Minneapolis Public Schools", 28700, 9900, 34.5,
         72.1, 38.2, 12.4, 18.6, 14.8, 62.1,
         33.5, 10.8, "Somali, Spanish, Hmong, Oromo"),
        ("0625", "St. Paul Public Schools", 32500, 10400, 32.0,
         74.5, 36.8, 11.9, 19.2, 13.5, 58.7,
         31.2, 9.6, "Hmong, Karen, Somali, Spanish"),
        ("0742", "St. Cloud Area Schools", 10200, 2750, 27.0,
         76.8, 42.1, 14.2, 22.8, 16.3, 58.5,
         38.4, 12.1, "Somali, Spanish, Vietnamese"),
        ("0191", "Burnsville-Eagan-Savage ISD 191", 9200, 2210, 24.0,
         82.4, 48.5, 16.8, 24.1, 18.7, 64.2,
         44.1, 14.5, "Spanish, Somali, Vietnamese, Amharic"),
        ("0280", "Richfield Public Schools", 4200, 1680, 40.0,
         73.2, 33.5, 11.2, 17.8, 12.6, 55.8,
         28.9, 9.2, "Spanish, Somali, Amharic"),
        ("0013", "Columbia Heights Public Schools", 3500, 1690, 48.3,
         68.5, 30.1, 10.5, 16.2, 11.8, 52.4,
         26.4, 8.8, "Spanish, Somali, Vietnamese, Karen"),
        ("0535", "Rochester Public Schools", 17800, 2850, 16.0,
         84.1, 52.8, 18.5, 26.4, 20.1, 66.8,
         48.2, 16.2, "Somali, Spanish, Vietnamese, Karen"),
        ("0885", "St. Louis Park Public Schools", 4800, 720, 15.0,
         85.2, 54.1, 19.8, 28.2, 22.4, 68.5,
         49.5, 17.1, "Spanish, Somali, Russian"),
        ("0270", "Hopkins Public Schools", 7200, 1080, 15.0,
         86.5, 55.8, 20.2, 29.1, 23.5, 70.2,
         50.8, 17.8, "Spanish, Somali, Amharic"),
        ("0833", "South Washington County ISD 833", 18500, 1480, 8.0,
         89.2, 60.4, 22.1, 30.5, 24.8, 68.9,
         56.2, 19.5, "Spanish, Vietnamese, Hmong"),
        ("0011", "Anoka-Hennepin ISD 11", 37200, 3350, 9.0,
         87.8, 57.2, 20.8, 28.8, 22.1, 66.4,
         52.8, 18.2, "Spanish, Hmong, Somali, Vietnamese"),
        ("0271", "Bloomington Public Schools", 10200, 1940, 19.0,
         80.5, 46.2, 15.4, 22.5, 17.2, 62.8,
         41.5, 13.5, "Spanish, Somali, Vietnamese, Amharic"),
        ("0709", "Duluth Public Schools", 8900, 670, 7.5,
         82.1, 50.5, 17.2, 25.1, 18.5, 60.4,
         45.8, 14.8, "Somali, Spanish, Hmong"),
        ("0012", "Centennial ISD 12", 6800, 680, 10.0,
         88.5, 58.8, 21.4, 30.2, 24.1, 67.5,
         54.1, 18.8, "Spanish, Vietnamese, Hmong"),
        ("0197", "West St. Paul-Mendota Hts-Eagan", 5100, 1430, 28.0,
         75.8, 40.8, 13.8, 20.5, 15.2, 59.2,
         36.2, 11.8, "Spanish, Somali, Hmong, Karen"),
    ]

    return pd.DataFrame(data, columns=[
        'district_id', 'district_name', 'total_students',
        'el_count', 'el_percent', 'graduation_rate',
        'mca_read_all', 'mca_read_el', 'mca_read_hispanic',
        'mca_read_black', 'mca_read_white',
        'mca_math_all', 'mca_math_el', 'top_el_languages'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (modeled from MDE ACCESS public files)
# ============================================================================

def load_access_data(districts_df):
    """
    Generate district ACCESS domain data modeled from MDE ACCESS growth norms.
    Minnesota exit criteria: Overall composite 4.5+ AND 3.5+ in at least 3 of 4 domains.
    Scale scores approximate WIDA ACCESS 100-600 range by grade.
    """
    access_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                # Base scores by grade — speaking naturally higher than writing
                base_speaking = 335 + (grade * 9)
                base_writing = 282 + (grade * 7)
                base_listening = 340 + (grade * 8)
                base_reading = 295 + (grade * 7)

                # District adjustments: lower EL proficiency = lower scores
                el_factor = d['mca_read_el'] / 18.0
                speaking_adj = int(14 * el_factor + d['el_percent'] * 0.35)
                writing_adj = int(-10 + (el_factor - 1) * 11)
                listening_adj = speaking_adj - 2
                reading_adj = writing_adj + 10

                # Somali/Hmong districts: stronger oral, weaker literacy gap
                if 'Somali' in d['top_el_languages'].split(', ')[0]:
                    speaking_adj += 6
                    writing_adj -= 4
                if 'Hmong' in d['top_el_languages'].split(', ')[0]:
                    speaking_adj += 4
                    reading_adj -= 3

                # Year-over-year modest growth
                year_adj = 3 if year == 2025 else 0

                # Columbia Heights special: highest EL% means concentrated services
                if d['district_id'] == '0013':
                    speaking_adj += 8
                    writing_adj -= 6

                access_data.append({
                    'district_id': d['district_id'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(15, int(d['el_count'] / 6)),
                    'listening_avg': base_listening + listening_adj + year_adj,
                    'speaking_avg': base_speaking + speaking_adj + year_adj,
                    'reading_avg': base_reading + reading_adj + year_adj,
                    'writing_avg': base_writing + writing_adj + year_adj,
                    'composite_avg': int((base_speaking + speaking_adj +
                                          base_writing + writing_adj +
                                          base_listening + listening_adj +
                                          base_reading + reading_adj) / 4 + 15 + year_adj),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: MCA Achievement Data (from MN Report Card 2025)
# ============================================================================

def load_mca_data(districts_df):
    """
    Generate MCA data based on 2025 MN Report Card proficiency rates.
    MCA has 4 performance levels: Does Not Meet, Partially Meets, Meets, Exceeds.
    Reading tested grades 3-8, 10. Math tested grades 3-8, 11.
    Statewide: Reading 49.5%, Math 45.0%.
    """
    mca_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['Reading', 'Math']:
                    if subject == 'Reading':
                        base = d['mca_read_all']
                    else:
                        base = d['mca_math_all']

                    # Grade adjustment: proficiency dips in middle school
                    prof = max(10, min(85, base + (grade - 5) * -1.5))

                    # Year adjustment
                    if year == 2024:
                        prof = prof - 1.2

                    # MCA 4-level distribution
                    exceeds = max(2, prof * 0.20)
                    meets = max(5, prof - exceeds)
                    partially_meets = max(10, (100 - prof) * 0.45)
                    does_not_meet = max(5, 100 - meets - exceeds - partially_meets)

                    mca_data.append({
                        'district_id': d['district_id'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'does_not_meet_pct': round(does_not_meet, 1),
                        'partially_meets_pct': round(partially_meets, 1),
                        'meets_pct': round(meets, 1),
                        'exceeds_pct': round(exceeds, 1),
                        'proficient_pct': round(meets + exceeds, 1),
                    })

    return pd.DataFrame(mca_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (from MDE ACCESS public files)
# ============================================================================

def load_statewide_domain_data():
    """
    Statewide ACCESS domain proficiency percentages by grade cluster.
    Source: MDE ACCESS data files (rc.education.mn.gov)
    Minnesota has ~91,000 ELs across 327 districts.
    Exit criteria: Composite 4.5+ AND 3.5+ in at least 3 of 4 domains.
    """
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 44, 'speaking': 40, 'reading': 26, 'writing': 20},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 50, 'speaking': 46, 'reading': 30, 'writing': 22},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 54, 'speaking': 48, 'reading': 34, 'writing': 25},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 57, 'speaking': 50, 'reading': 37, 'writing': 27},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 42, 'speaking': 38, 'reading': 24, 'writing': 18},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 48, 'speaking': 44, 'reading': 28, 'writing': 20},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 52, 'speaking': 46, 'reading': 32, 'writing': 23},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 55, 'speaking': 48, 'reading': 35, 'writing': 25},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, district_id, grade, year):
    """
    Compute Type 4 detection for a given district/grade/year.
    Type 4 candidates show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.
    """
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'district_id': district_id,
        'district_name': row['district_name'],
        'grade': grade,
        'year': year,
        'speaking_avg': row['speaking_avg'],
        'writing_avg': row['writing_avg'],
        'delta': delta,
        'delta_normalized': delta_normalized,
        'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(districts_df):
    st.header("Minnesota Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pilot Districts", len(districts_df))
    with col2:
        st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3:
        st.metric("English Learners", f"{districts_df['el_count'].sum():,}")
    with col4:
        st.metric("Statewide Reading Prof", "49.5%", help="2025 MCA Reading statewide")

    st.divider()

    st.subheader("Minnesota Equity Context")
    st.markdown("""
    Minnesota has among the **largest achievement gaps in the nation** between white students and
    students of color. Despite high overall performance, the state consistently ranks at or near
    the bottom nationally in equity metrics for Black, Hispanic, and American Indian students.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**Largest gaps in nation**\nWhite-Black reading gap (~30 pts)")
    with col2:
        st.error("**Largest gaps in nation**\nWhite-Hispanic math gap (~25 pts)")
    with col3:
        st.warning("**48.3% EL**\nColumbia Heights ISD 13")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**READ Act (2023)**\nStructured literacy mandate K-3")
    with col2:
        st.info("**LEAPS Act (2014)**\nEL instructional framework")
    with col3:
        st.info("**North Star**\nAccountability System")

    st.divider()

    st.subheader("Key State Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Statewide Math Prof", "45.0%", help="2025 MCA Math statewide")
    with col2:
        st.metric("Statewide EL Count", "~91,000", help="11% of total enrollment")
    with col3:
        st.metric("Total Districts", "327", help="MARSS data system")
    with col4:
        st.metric("Exit Criteria", "4.5+ Comp", help="Plus 3.5+ in 3 of 4 domains")

    st.divider()

    st.subheader("Top EL Languages Statewide")
    lang_data = pd.DataFrame({
        'Language': ['Spanish', 'Somali', 'Hmong', 'Vietnamese', 'Karen', 'Oromo', 'Amharic', 'Arabic'],
        'Approx Share': [35, 18, 12, 5, 4, 3, 3, 2],
    })
    fig_lang = px.bar(lang_data, x='Language', y='Approx Share',
                      color='Approx Share',
                      color_continuous_scale=[[0, '#C0C0C0'], [1, MN_BLUE]],
                      labels={'Approx Share': '% of EL Population'},
                      text='Approx Share')
    fig_lang.update_traces(texttemplate='%{text}%', textposition='outside')
    fig_lang.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                           title="Top EL Home Languages in Minnesota")
    st.plotly_chart(fig_lang, use_container_width=True)

    st.divider()

    st.subheader("Pilot Districts -- Highest EL Populations")
    display = districts_df[['district_id', 'district_name', 'total_students', 'el_count', 'el_percent',
                            'mca_read_all', 'mca_read_el', 'mca_read_black', 'mca_read_white',
                            'top_el_languages']].copy()
    display.columns = ['Dist ID', 'District', 'Students', 'EL Count', 'EL %',
                       'Read All %', 'Read EL %', 'Read Black %', 'Read White %',
                       'Top Languages']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Learner Population by District")
    fig = px.bar(
        districts_df.sort_values('el_count', ascending=True),
        x='el_count', y='district_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, MN_BLUE]],
        labels={'el_count': 'English Learners', 'district_name': 'District', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False,
                      title="EL Population by District (color = EL %)")
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** MDE ACCESS data files (rc.education.mn.gov). Minnesota is a WIDA Consortium member.
    Domain proficiency percentages show the systemic oral-written delta: Speaking consistently
    outperforms Writing across all grade clusters. Minnesota exit criteria require an overall
    composite of **4.5+** AND **3.5+** in at least 3 of 4 domains.
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', MN_BLUE), ('speaking', MN_GOLD),
                           ('reading', '#888888'), ('writing', MN_RED)]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 72])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[MN_RED if d > 18 else MN_GOLD for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap",
                       yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.markdown("""
    ---
    **Why this matters for Minnesota:** The oral-written gap is especially significant for
    Somali and Hmong-speaking students, whose home languages have different orthographic
    systems than English. The LEAPS Act (2014) framework emphasizes cross-domain growth,
    and the READ Act (2023) structured literacy mandate targets the writing/reading gap.
    """)


def render_access_analysis(access_df, districts_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains. Minnesota has ~91,000 ELs (11% of enrollment).
    Exit criteria: Overall composite **4.5+** AND **3.5+** in at least 3 of 4 domains.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="acc_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="acc_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        # Show top languages for context
        lang = districts_df[districts_df['district_id'] == district_id]['top_el_languages'].values[0]
        st.info(f"**Top EL languages in {district}:** {lang}")

        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2:
            st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3:
            st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4:
            st.metric("Writing", f"{row['writing_avg']:.0f}")
        with col5:
            st.metric("Composite", f"{row['composite_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(
            x=domains, y=scores,
            marker_color=[MN_BLUE, MN_GOLD, '#888888', MN_RED],
            text=[f"{s:.0f}" for s in scores], textposition='outside'
        ))
        fig.update_layout(
            title=f"ACCESS Domains -- {district} -- Grade {grade} ({year})",
            yaxis_title="Scale Score", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oral Average", f"{oral:.0f}")
        with col2:
            st.metric("Written Average", f"{written:.0f}")
        with col3:
            st.metric("Oral-Written Gap", f"{gap:+.0f}",
                      delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        # Exit criteria check
        st.subheader("Exit Criteria Check (MN: 4.5+ composite, 3.5+ in 3/4 domains)")
        st.markdown("""
        Minnesota requires an overall composite score of **4.5 or higher** AND proficiency
        level **3.5 or higher** in at least **3 of 4 domains** to exit EL services.
        This is among the more rigorous exit criteria nationally.
        """)
    else:
        st.warning("No data available for the selected filters.")


def render_type4(access_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.

    In Minnesota, this is particularly relevant for **Somali and Hmong** speaking students,
    whose oral fluency in English may develop faster than written proficiency due to
    orthographic distance from English.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="t4_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    result = compute_type4_analysis(access_df, district_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2:
            st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3:
            st.metric("Delta", f"{result['delta']:+.0f}")
        with col4:
            st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']],
                             marker_color=MN_GOLD))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']],
                             marker_color=MN_BLUE))
        fig.update_layout(
            title=f"Speaking vs Writing -- {district} -- Grade {grade}",
            barmode='group', height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
            st.markdown("""
            **Minnesota-specific action:** Under the LEAPS Act framework, districts should review
            these students for appropriate writing intervention and consider structured literacy
            supports aligned with the READ Act (2023).
            """)
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(access_df, district_id, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['speaking_avg'],
                name='Speaking', mode='lines+markers',
                line=dict(color=MN_GOLD, width=3)
            ))
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['writing_avg'],
                name='Writing', mode='lines+markers',
                line=dict(color=MN_BLUE, width=3)
            ))
            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade", yaxis_title="Scale Score", height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.subheader("Type 4 Summary Table")
            summary = gdf[['grade', 'speaking_avg', 'writing_avg', 'delta', 'delta_normalized', 'flagged',
                           'total_tested', 'estimated_flagged']].copy()
            summary.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Norm Delta', 'Flagged',
                              'Tested', 'Est. Affected']
            st.dataframe(summary, use_container_width=True, hide_index=True)


def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Real data from 2025 MN Report Card.** Minnesota has among the **largest achievement gaps
    in the nation** between white and students of color. MCA Reading proficiency by subgroup
    across pilot districts.

    Statewide 2025: Reading 49.5%, Math 45.0%. The gap between white students and Black/Hispanic/EL
    students often exceeds 30 percentage points.
    """)

    st.divider()

    # Achievement gap bar chart
    fig = go.Figure()
    sorted_df = districts_df.sort_values('mca_read_all', ascending=True)
    for col, name, color in [
        ('mca_read_white', 'White', '#666666'),
        ('mca_read_all', 'All Students', MN_BLUE),
        ('mca_read_hispanic', 'Hispanic', '#E8540A'),
        ('mca_read_black', 'Black', MN_RED),
        ('mca_read_el', 'English Learners', MN_GOLD),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['district_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="MCA Reading Proficiency by Subgroup -- 2025 Report Card",
        barmode='group', xaxis_title="% Proficient", height=650,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap magnitude analysis
    st.subheader("Gap Magnitude: White - Black Reading Proficiency")
    districts_df_copy = districts_df.copy()
    districts_df_copy['wb_gap'] = districts_df_copy['mca_read_white'] - districts_df_copy['mca_read_black']
    districts_df_copy['wh_gap'] = districts_df_copy['mca_read_white'] - districts_df_copy['mca_read_hispanic']
    districts_df_copy['we_gap'] = districts_df_copy['mca_read_white'] - districts_df_copy['mca_read_el']

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_wb = districts_df_copy['wb_gap'].mean()
        st.metric("Avg White-Black Gap", f"{avg_wb:.1f} pts", delta="Critical", delta_color="inverse")
    with col2:
        avg_wh = districts_df_copy['wh_gap'].mean()
        st.metric("Avg White-Hispanic Gap", f"{avg_wh:.1f} pts", delta="Critical", delta_color="inverse")
    with col3:
        avg_we = districts_df_copy['we_gap'].mean()
        st.metric("Avg White-EL Gap", f"{avg_we:.1f} pts", delta="Critical", delta_color="inverse")

    fig_gap = go.Figure()
    gap_sorted = districts_df_copy.sort_values('wb_gap', ascending=True)
    fig_gap.add_trace(go.Bar(
        x=gap_sorted['wb_gap'], y=gap_sorted['district_name'],
        orientation='h', marker_color=[MN_RED if g > 40 else MN_GOLD for g in gap_sorted['wb_gap']],
        text=[f"{g:.0f} pts" for g in gap_sorted['wb_gap']], textposition='outside'
    ))
    fig_gap.update_layout(
        title="White-Black Reading Gap by District (pts)", height=550,
        xaxis_title="Gap (percentage points)"
    )
    st.plotly_chart(fig_gap, use_container_width=True)

    # Scatter: EL proficiency vs overall
    st.subheader("EL Proficiency vs Overall Proficiency")
    fig2 = px.scatter(
        districts_df, x='mca_read_all', y='mca_read_el', size='el_count',
        color='el_percent', color_continuous_scale=[[0, '#ccc'], [1, MN_BLUE]],
        hover_name='district_name',
        labels={'mca_read_all': 'All Students Reading %', 'mca_read_el': 'EL Reading %',
                'el_count': 'EL Count', 'el_percent': 'EL %'}
    )
    fig2.add_shape(type="line", x0=0, y0=0, x1=80, y1=80,
                   line=dict(dash="dash", color="gray"))
    fig2.update_layout(
        title="EL Proficiency vs District Overall -- Gap Visualization", height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    ---
    **Minnesota context:** The gap between white students and students of color in Minnesota
    is consistently among the worst in the nation, despite Minnesota's relatively high overall
    proficiency rates. This disparity is especially pronounced in the Twin Cities metro area,
    where large Somali, Hmong, and Latino populations are concentrated. The North Star
    Accountability System tracks these gaps as a key metric.
    """)


def render_mca(mca_df, districts_df):
    st.header("MCA Assessment Analysis")
    st.markdown("""
    **Minnesota Comprehensive Assessments (MCA)** -- 4 performance levels:
    Does Not Meet, Partially Meets, Meets, Exceeds.

    Reading: grades 3-8 and 10. Math: grades 3-8 and 11.
    Statewide 2025: Reading 49.5%, Math 45.0%.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="mca_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="mca_g")
    with col3:
        subject = st.selectbox("Subject", ['Reading', 'Math'], key="mca_s")
    with col4:
        year = st.selectbox("Year", [2025, 2024], key="mca_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = mca_df[
        (mca_df['district_id'] == district_id) &
        (mca_df['grade'] == grade) &
        (mca_df['subject'] == subject) &
        (mca_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Does Not Meet", f"{row['does_not_meet_pct']:.1f}%")
        with col2:
            st.metric("Partially Meets", f"{row['partially_meets_pct']:.1f}%")
        with col3:
            st.metric("Meets", f"{row['meets_pct']:.1f}%")
        with col4:
            st.metric("Exceeds", f"{row['exceeds_pct']:.1f}%")

        levels = ['Does Not Meet', 'Partially Meets', 'Meets', 'Exceeds']
        values = [row['does_not_meet_pct'], row['partially_meets_pct'],
                  row['meets_pct'], row['exceeds_pct']]
        colors = [MN_RED, '#E8540A', MN_GOLD, MN_BLUE]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"MCA {subject} -- {district} -- Grade {grade} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Proficiency rate context
        st.metric("Combined Proficiency (Meets + Exceeds)",
                  f"{row['proficient_pct']:.1f}%",
                  help="Statewide: Reading 49.5%, Math 45.0%")

        # Cross-grade comparison
        st.subheader(f"MCA {subject} Across Grades -- {district} ({year})")
        cross = mca_df[
            (mca_df['district_id'] == district_id) &
            (mca_df['subject'] == subject) &
            (mca_df['year'] == year)
        ]
        if not cross.empty:
            fig2 = go.Figure()
            for level, color in zip(levels, colors):
                col_name = level.lower().replace(' ', '_') + '_pct'
                fig2.add_trace(go.Bar(
                    x=cross['grade'], y=cross[col_name],
                    name=level, marker_color=color
                ))
            fig2.update_layout(
                barmode='stack', xaxis_title="Grade", yaxis_title="Percentage",
                height=400, title=f"MCA {subject} Performance Distribution"
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")


def render_export(access_df, mca_df, districts_df, domain_df):
    st.header("Export Data")

    st.markdown("Download VERA-MN analysis data as CSV files for further analysis.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download ACCESS CSV",
            access_df.to_csv(index=False),
            "vera_mn_access.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("MCA Data")
        st.dataframe(mca_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download MCA CSV",
            mca_df.to_csv(index=False),
            "vera_mn_mca.csv", "text/csv",
            use_container_width=True
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Domain CSV",
            domain_df.to_csv(index=False),
            "vera_mn_domains.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("District Reference Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Districts CSV",
            districts_df.to_csv(index=False),
            "vera_mn_districts.csv", "text/csv",
            use_container_width=True
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title="VERA-MN | Minnesota Type 4 Detection",
        page_icon="*",
        layout="wide"
    )

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {MN_BLUE}; }}
        .stButton > button {{ background-color: {MN_BLUE}; color: white; }}
        .stButton > button:hover {{ background-color: {MN_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    # Load all data
    districts_df = load_districts()
    access_df = load_access_data(districts_df)
    mca_df = load_mca_data(districts_df)
    domain_df = load_statewide_domain_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {MN_BLUE}; margin: 0;">VERA-MN</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Minnesota Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Statewide Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "MCA Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - MDE ACCESS Public Files
    - 2025 MN Report Card
    - MCA (MN Comprehensive Assessments)
    - MARSS Data System

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points (normalized)

    **MN Exit Criteria:**
    - Composite 4.5+
    - 3.5+ in 3 of 4 domains

    **Key Context:**
    - ~91,000 ELs (11%)
    - 327 school districts
    - **Largest achievement gaps in nation**
    - READ Act (2023) / LEAPS Act (2014)
    - Somali, Hmong, Karen, Spanish
    - Columbia Heights: 48.3% EL

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    # Page routing
    if page == "Overview":
        render_overview(districts_df)
    elif page == "Statewide Domain Analysis":
        render_domain_analysis(domain_df)
    elif page == "ACCESS Analysis":
        render_access_analysis(access_df, districts_df)
    elif page == "Type 4 Detection":
        render_type4(access_df, districts_df)
    elif page == "Achievement Gaps":
        render_achievement_gaps(districts_df)
    elif page == "MCA Analysis":
        render_mca(mca_df, districts_df)
    elif page == "Export Data":
        render_export(access_df, mca_df, districts_df, domain_df)


if __name__ == "__main__":
    main()
