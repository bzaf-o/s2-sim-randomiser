import pandas as pd
import sqlite3 as sql3
import random
import streamlit as st

class LegacyRandomiser:

    def __init__(self, csv_path="data.csv", db_path='data.db'):
        # Initialize the randomiser with data loading and database connection
        try:
            self.data = self._load_and_validate_data(csv_path)
            self.conn = sql3.connect(db_path)
            self.cursor = self.conn.cursor()
            self._init_db()
        
        except Exception as e:
            st.error(f"Initialization Error: {e}")

    def _load_and_validate_data(self, csv_path):
        # Load CSV validate data again
       try:
            df = pd.read_csv(csv_path) 
            # Mapping the actual column names from the CSV to the expected names
            column_mapping = {
                'hood': 'Neighbourhood',
                'sex': 'Sex',
                'startage': 'Starting Age',
                'skin': 'Skin Tone',
                'fitness': 'Fitness',
                'haircol': 'Hair Colour',
                'eyecol': 'Eye Colour',
                'aspiration': 'Aspiration',
                'secaspiration': 'Secondary Aspiration',
                'turnon': 'Turn Ons',
                'turnoff': 'Turn Offs',
                'career': 'Career',
                'university': 'University Major',
                'personalcol': 'Personal Colour'
            }
            
            df = df.rename(columns=column_mapping)

            # Check for required columns
            required_columns = list(column_mapping.values())
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

            return df
       
       except pd.errors.EmptyDataError:
        st.error("CSV file is empty. Please check your data source.")
        return pd.DataFrame()
       
       except Exception as e:
        st.error(f"Data Loading Error: {e}")
        return pd.Data.Frame()

    def _init_db(self):
        try:
            self.cursor.execute("DROP TABLE IF EXISTS sim_data")
            
            # Create columns dynamically based on DataFrame
            columns = ', '.join([f'"{col}" TEXT' for col in self.data.columns])
            create_table_query = f'''
                CREATE TABLE sim_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {columns}
                )
            '''
            self.cursor.execute(create_table_query)

            # Insert data into the table
            for _, row in self.data.iterrows():
                placeholders = ', '.join(['?'] * len(self.data.columns))
                insert_query = f'INSERT INTO sim_data ({", ".join(f"`{col}`" for col in self.data.columns)}) VALUES ({placeholders})'
                
                # Convert row to list and replace NaN with None
                row_values = [None if pd.isna(val) else str(val) for val in row]
                
                self.cursor.execute(insert_query, row_values)

            self.conn.commit()

        except Exception as e:
            st.error(f"Database Initialization Error: {e}")

    def gen_personality(self):
        
        # Generate random personality points ranging between 0 to 10, total max = 25
        traits = ['Neat', 'Outgoing', 'Active', 'Playful', 'Nice']
        points = [random.randint(0, 10) for _ in range(5)]
        total = sum(points)
        
        while total > 25:
            max_idx = points.index(max(points))
            points[max_idx] -= 1
            total -= 1
        
        return dict(zip(traits, points))

    def generate_sim(self, selected_features=None):
        # Generates a random sim

        if selected_features is None:
            selected_features = {
                'Neighbourhood': True, 'Sex': True, 'Starting Age': True, 'Skin Tone': True, 
                'Fitness': True, 'Hair Colour': True, 'Eye Colour': True, 'Aspiration': True, 'Secondary Aspiration': True,
                'Turn Ons': True, 'Turn Offs': True, 'Career': True, 'University Major': True, 
                'Personal Colour': True, 'Glasses': True, 'Beard': True, 'Married': True, 
                'Children': True, 'Employed Spouse': True, 'Personality': True
            }

        sim = {}

        feature_column_map = {
            'Neighbourhood': 'Neighbourhood',
            'Sex': 'Sex',
            'Starting Age': 'Starting Age',
            'Skin Tone': 'Skin Tone',
            'Fitness': 'Fitness',
            'Hair Colour': 'Hair Colour',
            'Eye Colour': 'Eye Colour',
            'Aspiration': 'Aspiration',
            'Secondary Aspiration': 'Secondary Aspiration',
            'Turn Ons': 'Turn Ons',
            'Turn Offs': 'Turn Offs',
            'Career': 'Career',
            'University Major': 'University Major',
            'Personal Colour': 'Personal Colour'
        }

        # Randomisation
        for feature, is_selected in selected_features.items():
            if is_selected and feature in feature_column_map:
                column = feature_column_map[feature]
                unique_values = self.data[column].dropna().unique().tolist()
                
                if unique_values:
                    if feature in ['Turn Ons', 'Turn Offs']:
                        if feature == 'Turn Ons':
                            # Select two unique turn ons
                            first_turn_on = random.choice(unique_values)
                            remaining_turn_ons = [to for to in unique_values if to != first_turn_on]
                            second_turn_on = random.choice(remaining_turn_ons)
                            sim['Turn Ons'] = [first_turn_on, second_turn_on]
                        else:
                            # Select a turn off that doesn't conflict with turn ons
                            turn_offs = [to for to in unique_values if to not in sim.get('Turn Ons', [])]
                            sim['Turn Offs'] = [random.choice(turn_offs)] if turn_offs else []
                    elif feature == 'Secondary Aspiration':
                        primary_aspiration = sim.get('Aspiration')
                        if primary_aspiration:
                            # Filter out primary aspiration from secondary options
                            sec_options = [asp for asp in unique_values if asp != primary_aspiration]
                            sim[feature] = random.choice(sec_options) if sec_options else primary_aspiration
                        else:
                            sim[feature] = random.choice(unique_values)
                    else:
                        sim[feature] = random.choice(unique_values)

        if selected_features.get('Glasses', False):
            sim['Glasses'] = random.choice([True, False])

        if selected_features.get('Beard', False):
            sim['Beard'] = random.choice([True, False])

        if selected_features.get('Married', False):
            sim['Married'] = random.choice([True, False])

        if selected_features.get('Children', False):
            children_max = 6  # Default max if can't get from data
            if 'kids' in self.data.columns and self.data['kids'].notna().any():
                children_max = int(self.data['kids'].max())
            sim['Children'] = random.randint(1, children_max)

        if selected_features.get('Employed Spouse', False):
            sim['Employed Spouse'] = random.choice([True, False])

        if selected_features.get('Personality', False):
            sim['Personality Points'] = self.gen_personality()

        return sim

def create_points_display(points):
    # Convert personality points to bar display with point count

    return f"{'🟦 ' * points}({points})"

def generate_sim_txt_report(sim):
    # Generate a text file of the Sim's details

    report = "Randomised Sim\n"
    report += "=" * 30 + "\n\n"
    
    # Basic sections
    sections = {
        "Basic Details": [
            "Neighbourhood", "Sex", "Starting Age", 
            "Skin Tone", "Fitness"
        ],
        "Personal Details": [
            "Hair Colour", "Eye Colour", 
            "Career", "University Major", "Aspiration"
        ],
        "Interests": ["Turn Ons", "Turn Offs", "Personal Colour"],
        "Others": [
            "Glasses", "Beard", "Married", 
            "Children", "Employed Spouse"
        ]
    }
    
    for section, keys in sections.items():
        report += f"{section}:\n"
        for key in keys:
            if key in sim:
                value = sim[key]
                if isinstance(value, list):
                    value = ', '.join(map(str, value))
                elif isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                report += f"- {key}: {value}\n"
        report += "\n"
    
    # Personality Points
    if 'Personality Points' in sim:
        report += "Personality Points:\n"
        for trait, points in sim['Personality Points'].items():
            report += f"- {trait}: {points} points\n"
    
    return report

def main():
    st.set_page_config(
        page_title="Sims 2 Randomiser", 
        page_icon="🎲", 
        initial_sidebar_state="auto",
        layout="centered"
    )
    
    # Dark Mode CSS with centered buttons
    st.markdown("""
    <style>
    .stButton {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .stButton>button {
        margin: 0 auto;
    }
    .section-header {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        text-align: center;
        font-weight: bold;
    }
    .section-header-1 { background-color: #9a2617; }  /* Red */
    .section-header-2 { background-color: #da6213; }  /* Orange */
    .section-header-3 { background-color: #93a661; }  /* Green */
    .section-header-4 { background-color: #1496bb; }  /* Blue */
    </style>
    """, unsafe_allow_html=True)
    
    st.title('🎲 Sims 2 Randomiser')
    st.info("*Randomise a unique Sim for your next playthrough! Use the checkboxes on the right sidebar to choose which aspects to randomise.*")
    
    # Initialize randomiser
    try:
        randomiser = LegacyRandomiser()
        
        # Sidebar for feature selection
        st.sidebar.header("Features")
        
        # Feature checkboxes
        features = {
            'Neighbourhood': st.sidebar.checkbox('Neighbourhood', value=True),
            'Sex': st.sidebar.checkbox('Sex', value=True),
            'Starting Age': st.sidebar.checkbox('Starting Age', value=True),
            'Skin Tone': st.sidebar.checkbox('Skin Tone', value=True),
            'Fitness': st.sidebar.checkbox('Fitness', value=True),
            'Hair Colour': st.sidebar.checkbox('Hair Colour', value=True),
            'Eye Colour': st.sidebar.checkbox('Eye Colour', value=True),
            'Aspiration': st.sidebar.checkbox('Aspiration', value=True),
            'Secondary Aspiration': st.sidebar.checkbox('Secondary Aspiration', value=True),
            'Turn Ons': st.sidebar.checkbox('Turn Ons', value=True),
            'Turn Offs': st.sidebar.checkbox('Turn Offs', value=True),
            'Career': st.sidebar.checkbox('Career', value=True),
            'University Major': st.sidebar.checkbox('University Major', value=True),
            'Glasses': st.sidebar.checkbox('Glasses', value=True),
            'Beard': st.sidebar.checkbox('Beard', value=True),
            'Married': st.sidebar.checkbox('Married', value=True),
            'Children': st.sidebar.checkbox('Children', value=True),
            'Employed Spouse': st.sidebar.checkbox('Employed Spouse', value=True),
            'Personality': st.sidebar.checkbox('Personality', value=True),
            'Personal Colour': st.sidebar.checkbox('Personal Colour', value=True)
            
        }
        
        # Columns for centered buttons
        col1, col2, col3 = st.columns([1,2,1])
        
        with col2:
            generate_clicked = st.button('🟢 Generate Sim')
        
        if generate_clicked:
            st.markdown("---")

        # Store sim in session state to enable download
        if 'generated_sim' not in st.session_state:
            st.session_state.generated_sim = None
        
        # Generate Sim
        if generate_clicked:
            # Pass selected features to generate_sim method
            st.session_state.generated_sim = randomiser.generate_sim(features)
        
        # Display generated Sim
        if st.session_state.generated_sim:
            sim = st.session_state.generated_sim
            
            # Custom header
            def colored_header(text, color_class):
                st.markdown(f'<div class="section-header {color_class}">{text}</div>', unsafe_allow_html=True)
            
            # Reorganized to show balanced info in columns
            col1, col2 = st.columns(2)
            
            with col1:
                colored_header('Basic & Personal Details', 'section-header-1')
                details = [
                    ('Neighbourhood', sim.get('Neighbourhood')),
                    ('Sex', sim.get('Sex')),
                    ('Starting Age', sim.get('Starting Age')),
                    ('Skin Tone', sim.get('Skin Tone')),
                    ('Fitness', sim.get('Fitness')),
                    ('Hair Colour', sim.get('Hair Colour')),
                    ('Eye Colour', sim.get('Eye Colour')),
                ]
                for label, value in details:
                    if value is not None:
                        st.write(f"**{label}:** {value}")
            
            with col2:
                colored_header('Career, Aspirations & Interests', 'section-header-2')
                details = [
                    ('Career', sim.get('Career')),
                    ('University Major', sim.get('University Major')),
                    ('Aspiration', sim.get('Aspiration')),
                    ('Secondary Aspiration', sim.get('Secondary Aspiration')),
                    ('Turn Ons', ', '.join(sim.get('Turn Ons', []))),
                    ('Turn Offs', ', '.join(sim.get('Turn Offs', []))),
                ]
                for label, value in details:
                    if value is not None and value != '':
                        st.write(f"**{label}:** {value}")
            
            # Personality and Others in a single row
            col3, col4 = st.columns(2)
            
            with col3:
                colored_header('Personality Points', 'section-header-3')
                if 'Personality Points' in sim:
                    for trait, points in sim['Personality Points'].items():
                        st.write(f"{trait}: {create_points_display(points)}")
            
            with col4:
                colored_header('Additional Details', 'section-header-4')
                others = [
                    ('Glasses?', sim.get('Glasses')),
                    ('Beard?', sim.get('Beard')),
                    ('Married?', sim.get('Married')),
                    ('No. of Children', sim.get('Children')),
                    ('Employed Spouse?', sim.get('Employed Spouse')),
                    ('Personal Colour?', sim.get('Personal Colour'))
                ]
                for label, value in others:
                    if value is not None:
                        display_value = 'Yes' if value is True else 'No' if value is False else value
                        st.write(f"**{label}:** {display_value}")
            
            st.markdown("---")
            
            # Download info button
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.download_button(
                    label="📥 Download Sim Details",
                    data=generate_sim_txt_report(sim),
                    file_name="sim_0.txt",
                    mime="text/plain"
                )
  
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()