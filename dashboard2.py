import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# =====================================================================
# EMPLOYEE KPI ANALYSIS SYSTEM
# =====================================================================

class EmployeeKPIAnalysis:
    """
    Comprehensive KPI Analysis for Employee Data
    Calculates Career Cluster, Promotion Gap, Retention, Training Needs, etc.
    """
    
    def __init__(self, csv_file_path):
        """Initialize with CSV file"""
        self.df = pd.read_csv(csv_file_path)
        self.kpi_results = {}
        self.prepare_data()
    
    def prepare_data(self):
        """Prepare and clean data"""
        # Handle any missing values
        self.df = self.df.fillna(0)
        
        # Ensure numeric columns
        numeric_cols = ['Age', 'MonthlyIncome', 'YearsAtCompany', 'YearsInCurrentRole',
                       'YearsSinceLastPromotion', 'TotalWorkingYears', 'TrainingTimesLastYear',
                       'PerformanceRating', 'JobSatisfaction', 'EnvironmentSatisfaction',
                       'Pramotion gap ratio', 'Role Stagnation Index', 'Training Intensity Score',
                       'Manager Stability Indicator']
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
    
    # =====================================================================
    # 1. CAREER CLUSTER ANALYSIS
    # =====================================================================
    
    def calculate_career_cluster(self):
        """
        Categorize employees into career trajectory types
        Returns: Career Cluster with 5 categories
        """
        conditions = []
        labels = []
        
        # High Performers - Rapid Growth Track
        high_performer = (
            (self.df['PerformanceRating'] >= 3.5) & 
            (self.df['JobLevel'] >= 3) &
            (self.df['YearsSinceLastPromotion'] <= 2)
        )
        
        # Rising Stars - Growth Potential
        rising_star = (
            (self.df['PerformanceRating'] >= 3) & 
            (self.df['JobLevel'] >= 2) &
            (self.df['YearsInCurrentRole'] <= 3)
        )
        
        # Core Contributors - Steady Performers
        core_contributor = (
            (self.df['PerformanceRating'] >= 2.5) & 
            (self.df['Attrition'] == 0) &
            (self.df['YearsAtCompany'] >= 5)
        )
        
        # At Risk - Potential Flight Risk
        at_risk = (
            (self.df['Attrition'] == 1) | 
            (self.df['JobSatisfaction'] <= 1) |
            (self.df['EnvironmentSatisfaction'] <= 1)
        )
        
        # Needs Development - Performance Issues
        needs_dev = (
            (self.df['PerformanceRating'] < 2.5) |
            (self.df['JobSatisfaction'] <= 2)
        )
        
        self.df['Career_Cluster'] = 'Core Contributor'
        self.df.loc[high_performer, 'Career_Cluster'] = 'High Performer'
        self.df.loc[rising_star, 'Career_Cluster'] = 'Rising Star'
        self.df.loc[at_risk, 'Career_Cluster'] = 'At Risk'
        self.df.loc[needs_dev, 'Career_Cluster'] = 'Needs Development'
        
        return self.df[['Employe Id', 'Career_Cluster']]
    
    # =====================================================================
    # 2. PROMOTION GAP SCORE & RISK OF STAGNATION
    # =====================================================================
    
    def calculate_promotion_gap_score(self):
        """
        Calculate Promotion Gap Score: Risk of Stagnation
        Based on: Years since promotion, Performance, Experience
        Scale: 0-100 (Higher = Higher Risk)
        """
        # Normalize components to 0-1 scale
        years_since_promo = self.df['YearsSinceLastPromotion']
        max_years = years_since_promo.max() if years_since_promo.max() > 0 else 1
        promo_risk = (years_since_promo / max_years) * 100
        
        # Performance factor (inverse - lower performance = higher risk)
        perf_risk = (5 - self.df['PerformanceRating']) * 20
        
        # Current role stagnation
        role_tenure = self.df['YearsInCurrentRole']
        max_tenure = role_tenure.max() if role_tenure.max() > 0 else 1
        role_risk = (role_tenure / max_tenure) * 100 * 0.5
        
        # Combined promotion gap score
        promotion_gap_score = (promo_risk * 0.5 + perf_risk * 0.3 + role_risk * 0.2)
        self.df['Promotion_Gap_Score'] = promotion_gap_score.clip(0, 100)
        
        # Categorize risk level
        self.df['Stagnation_Risk'] = pd.cut(
            self.df['Promotion_Gap_Score'],
            bins=[0, 30, 60, 100],
            labels=['Low', 'Medium', 'High']
        )
        
        return self.df[['Employe Id', 'Promotion_Gap_Score', 'Stagnation_Risk']]
    
    # =====================================================================
    # 3. RETENTION OPPORTUNITY INDEX
    # =====================================================================
    
    def calculate_retention_index(self):
        """
        Calculate Retention Opportunity Index (0-100)
        Higher score = Higher retention risk
        """
        # Factor 1: Attrition history (0-30 points)
        attrition_score = self.df['Attrition'] * 30
        
        # Factor 2: Job satisfaction (0-25 points)
        satisfaction_score = (5 - self.df['JobSatisfaction']) * 5
        
        # Factor 3: Environment satisfaction (0-25 points)
        env_satisfaction_score = (5 - self.df['EnvironmentSatisfaction']) * 5
        
        # Factor 4: Tenure (0-20 points - newer employees at higher risk)
        tenure_factor = 100 / (self.df['YearsAtCompany'] + 1)
        tenure_score = (tenure_factor / 100) * 20
        
        # Combined retention opportunity index
        retention_index = (attrition_score * 0.3 + satisfaction_score * 0.25 + 
                          env_satisfaction_score * 0.25 + tenure_score * 0.2)
        
        self.df['Retention_Opportunity_Index'] = retention_index.clip(0, 100)
        
        # Priority categorization
        self.df['Retention_Priority'] = pd.cut(
            self.df['Retention_Opportunity_Index'],
            bins=[0, 25, 50, 75, 100],
            labels=['Monitor', 'Engage', 'Intervene', 'Critical']
        )
        
        return self.df[['Employe Id', 'Retention_Opportunity_Index', 'Retention_Priority']]
    
    # =====================================================================
    # 4. TRAINING NEED INDICATOR & DEVELOPMENT PLANNING
    # =====================================================================
    
    def calculate_training_needs(self):
        """
        Calculate Training Need Indicator
        Identifies skill gap and development priorities
        """
        # Factor 1: Current training frequency (0-30 points)
        training_frequency = self.df['TrainingTimesLastYear']
        max_training = training_frequency.max() if training_frequency.max() > 0 else 1
        training_gap = (1 - (training_frequency / max_training)) * 30
        
        # Factor 2: Performance gaps (0-30 points)
        performance_gap = (5 - self.df['PerformanceRating']) * 6
        
        # Factor 3: Role progression readiness (0-25 points)
        job_involvement = self.df['JobInvolvement']
        max_involvement = job_involvement.max() if job_involvement.max() > 0 else 1
        progression_readiness = ((max_involvement - job_involvement) / max_involvement) * 25
        
        # Factor 4: Experience level (0-15 points - less experienced need more training)
        experience_factor = 100 / (self.df['TotalWorkingYears'] + 1)
        experience_score = (experience_factor / 100) * 15
        
        # Combined training need indicator
        training_need_indicator = (training_gap * 0.3 + performance_gap * 0.3 + 
                                  progression_readiness * 0.25 + experience_score * 0.15)
        
        self.df['Training_Need_Indicator'] = training_need_indicator.clip(0, 100)
        
        # Development planning categories
        self.df['Development_Plan'] = pd.cut(
            self.df['Training_Need_Indicator'],
            bins=[0, 25, 50, 75, 100],
            labels=['Maintenance', 'Basic Development', 'Advanced Training', 'Intensive Program']
        )
        
        return self.df[['Employe Id', 'Training_Need_Indicator', 'Development_Plan']]
    
    # =====================================================================
    # 5. MANAGER STABILITY IMPACT & LEADERSHIP INSIGHT
    # =====================================================================
    
    def calculate_manager_stability(self):
        """
        Calculate Manager Stability Impact on employee performance
        """
        # Factor 1: Years with current manager
        years_with_manager = self.df['YearsWithCurrManager']
        max_manager_tenure = years_with_manager.max() if years_with_manager.max() > 0 else 1
        manager_tenure_score = (years_with_manager / max_manager_tenure) * 40
        
        # Factor 2: Work-life balance impact (inverse relationship)
        worklife_balance = self.df['WorkLifeBalance']
        max_balance = worklife_balance.max() if worklife_balance.max() > 0 else 1
        balance_score = (worklife_balance / max_balance) * 30
        
        # Factor 3: Job satisfaction under current manager
        satisfaction_score = self.df['JobSatisfaction'] * 20
        
        # Factor 4: Performance under current manager
        performance_score = self.df['PerformanceRating'] * 10
        
        # Combined manager stability impact
        manager_stability_impact = (manager_tenure_score * 0.4 + balance_score * 0.3 + 
                                   satisfaction_score * 0.2 + performance_score * 0.1)
        
        self.df['Manager_Stability_Impact'] = manager_stability_impact.clip(0, 100)
        
        # Leadership effectiveness
        self.df['Leadership_Insight'] = pd.cut(
            self.df['Manager_Stability_Impact'],
            bins=[0, 25, 50, 75, 100],
            labels=['Needs Improvement', 'Developing', 'Effective', 'Highly Effective']
        )
        
        return self.df[['Employe Id', 'Manager_Stability_Impact', 'Leadership_Insight']]
    
    # =====================================================================
    # 6. INTERVENTION PRIORITY MATRIX
    # =====================================================================
    
    def calculate_intervention_priority(self):
        """
        Calculate overall intervention priority using multiple factors
        """
        # Combine all risk factors
        self.df['Intervention_Priority_Score'] = (
            self.df['Promotion_Gap_Score'] * 0.25 +
            self.df['Retention_Opportunity_Index'] * 0.35 +
            self.df['Training_Need_Indicator'] * 0.20 +
            (100 - self.df['Manager_Stability_Impact']) * 0.20
        )
        
        # Priority levels
        self.df['Intervention_Priority'] = pd.cut(
            self.df['Intervention_Priority_Score'],
            bins=[0, 30, 50, 70, 100],
            labels=['Low Priority', 'Medium Priority', 'High Priority', 'Critical']
        )
        
        return self.df[['Employe Id', 'Intervention_Priority_Score', 'Intervention_Priority']]
    
    # =====================================================================
    # 7. COMPREHENSIVE KPI DASHBOARD
    # =====================================================================
    
    def generate_all_kpis(self):
        """Generate all KPIs"""
        print("Generating Employee KPIs...")
        
        self.calculate_career_cluster()
        self.calculate_promotion_gap_score()
        self.calculate_retention_index()
        self.calculate_training_needs()
        self.calculate_manager_stability()
        self.calculate_intervention_priority()
        
        print("✓ All KPIs generated successfully!")
        
        return self.df
    
    # =====================================================================
    # 8. SUMMARY STATISTICS
    # =====================================================================
    
    def get_summary_statistics(self):
        """Generate summary statistics for all KPIs"""
        summary = {
            'Total Employees': len(self.df),
            'Attrition Rate': f"{(self.df['Attrition'].sum() / len(self.df) * 100):.2f}%",
            
            'Career Cluster Distribution': self.df['Career_Cluster'].value_counts().to_dict(),
            'Avg Promotion Gap Score': f"{self.df['Promotion_Gap_Score'].mean():.2f}",
            'Employees at High Stagnation Risk': len(self.df[self.df['Stagnation_Risk'] == 'High']),
            
            'Avg Retention Opportunity Index': f"{self.df['Retention_Opportunity_Index'].mean():.2f}",
            'Critical Retention Cases': len(self.df[self.df['Retention_Priority'] == 'Critical']),
            
            'Avg Training Need Indicator': f"{self.df['Training_Need_Indicator'].mean():.2f}",
            'Employees Needing Intensive Training': len(self.df[self.df['Development_Plan'] == 'Intensive Program']),
            
            'Avg Manager Stability Impact': f"{self.df['Manager_Stability_Impact'].mean():.2f}",
            'Highly Effective Managers': len(self.df[self.df['Leadership_Insight'] == 'Highly Effective']),
            
            'Critical Intervention Cases': len(self.df[self.df['Intervention_Priority'] == 'Critical']),
            'High Priority Cases': len(self.df[self.df['Intervention_Priority'] == 'High Priority']),
        }
        
        return summary
    
    # =====================================================================
    # 9. VISUALIZATION FUNCTIONS
    # =====================================================================
    
    def create_visualizations(self, output_dir='kpi_charts'):
        """Create comprehensive KPI visualizations"""
        import os
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (15, 10)
        
        # 1. Career Cluster Distribution
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Career Cluster
        career_counts = self.df['Career_Cluster'].value_counts()
        axes[0, 0].pie(career_counts.values, labels=career_counts.index, autopct='%1.1f%%',
                       colors=sns.color_palette("husl", len(career_counts)))
        axes[0, 0].set_title('Career Cluster Distribution', fontsize=12, fontweight='bold')
        
        # Promotion Gap Score Distribution
        axes[0, 1].hist(self.df['Promotion_Gap_Score'], bins=30, color='skyblue', edgecolor='black')
        axes[0, 1].axvline(self.df['Promotion_Gap_Score'].mean(), color='red', linestyle='--', 
                          linewidth=2, label=f"Mean: {self.df['Promotion_Gap_Score'].mean():.2f}")
        axes[0, 1].set_xlabel('Promotion Gap Score')
        axes[0, 1].set_ylabel('Number of Employees')
        axes[0, 1].set_title('Promotion Gap Score Distribution', fontsize=12, fontweight='bold')
        axes[0, 1].legend()
        
        # Stagnation Risk
        stagnation_counts = self.df['Stagnation_Risk'].value_counts()
        axes[0, 2].bar(stagnation_counts.index, stagnation_counts.values,
                      color=['green', 'orange', 'red'])
        axes[0, 2].set_ylabel('Number of Employees')
        axes[0, 2].set_title('Stagnation Risk Distribution', fontsize=12, fontweight='bold')
        
        # Retention Opportunity Index
        axes[1, 0].hist(self.df['Retention_Opportunity_Index'], bins=30, color='coral', edgecolor='black')
        axes[1, 0].axvline(self.df['Retention_Opportunity_Index'].mean(), color='red', linestyle='--',
                          linewidth=2, label=f"Mean: {self.df['Retention_Opportunity_Index'].mean():.2f}")
        axes[1, 0].set_xlabel('Retention Opportunity Index')
        axes[1, 0].set_ylabel('Number of Employees')
        axes[1, 0].set_title('Retention Opportunity Distribution', fontsize=12, fontweight='bold')
        axes[1, 0].legend()
        
        # Intervention Priority
        priority_counts = self.df['Intervention_Priority'].value_counts()
        axes[1, 1].barh(priority_counts.index, priority_counts.values,
                       color=['green', 'yellow', 'orange', 'red'])
        axes[1, 1].set_xlabel('Number of Employees')
        axes[1, 1].set_title('Intervention Priority Matrix', fontsize=12, fontweight='bold')
        
        # Training Need Indicator
        axes[1, 2].hist(self.df['Training_Need_Indicator'], bins=30, color='lightgreen', edgecolor='black')
        axes[1, 2].axvline(self.df['Training_Need_Indicator'].mean(), color='red', linestyle='--',
                          linewidth=2, label=f"Mean: {self.df['Training_Need_Indicator'].mean():.2f}")
        axes[1, 2].set_xlabel('Training Need Indicator')
        axes[1, 2].set_ylabel('Number of Employees')
        axes[1, 2].set_title('Training Need Distribution', fontsize=12, fontweight='bold')
        axes[1, 2].legend()
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/kpi_dashboard.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/kpi_dashboard.png")
        plt.close()
        
        # 2. Correlation Heatmap
        kpi_columns = ['Promotion_Gap_Score', 'Retention_Opportunity_Index',
                      'Training_Need_Indicator', 'Manager_Stability_Impact',
                      'Intervention_Priority_Score']
        correlation_matrix = self.df[kpi_columns].corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   fmt='.2f', square=True, linewidths=1)
        plt.title('KPI Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/kpi_correlation.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/kpi_correlation.png")
        plt.close()
        
        # 3. Scatter plot: Retention vs Promotion Gap
        plt.figure(figsize=(12, 8))
        colors = {'At Risk': 'red', 'High Performer': 'green', 'Rising Star': 'blue',
                 'Core Contributor': 'gray', 'Needs Development': 'orange'}
        for cluster in self.df['Career_Cluster'].unique():
            mask = self.df['Career_Cluster'] == cluster
            plt.scatter(self.df[mask]['Promotion_Gap_Score'],
                       self.df[mask]['Retention_Opportunity_Index'],
                       label=cluster, s=100, alpha=0.6,
                       color=colors.get(cluster, 'black'))
        
        plt.xlabel('Promotion Gap Score (Higher = More Stagnation)', fontsize=11)
        plt.ylabel('Retention Opportunity Index (Higher = Flight Risk)', fontsize=11)
        plt.title('Retention Risk vs Career Stagnation', fontsize=14, fontweight='bold')
        plt.legend(loc='best')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/retention_vs_stagnation.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/retention_vs_stagnation.png")
        plt.close()
    
    # =====================================================================
    # 10. EXPORT FUNCTIONS
    # =====================================================================
    
    def export_kpi_report(self, output_file='employee_kpi_report.xlsx'):
        """Export comprehensive KPI report to Excel"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet 1: Complete KPI Data
            kpi_export = self.df[['Employe Id', 'Age', 'Department', 'JobRole',
                                  'Career_Cluster', 'Promotion_Gap_Score', 'Stagnation_Risk',
                                  'Retention_Opportunity_Index', 'Retention_Priority',
                                  'Training_Need_Indicator', 'Development_Plan',
                                  'Manager_Stability_Impact', 'Leadership_Insight',
                                  'Intervention_Priority_Score', 'Intervention_Priority']]
            kpi_export.to_excel(writer, sheet_name='Employee KPIs', index=False)
            
            # Sheet 2: Summary Statistics
            summary_df = pd.DataFrame(self.get_summary_statistics().items(),
                                     columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Sheet 3: High Priority Cases
            high_priority = self.df[self.df['Intervention_Priority'] == 'Critical'].copy()
            high_priority.to_excel(writer, sheet_name='Critical Cases', index=False)
            
            # Sheet 4: Career Cluster Analysis
            cluster_analysis = self.df.groupby('Career_Cluster').agg({
                'Employe Id': 'count',
                'Promotion_Gap_Score': 'mean',
                'Retention_Opportunity_Index': 'mean',
                'Training_Need_Indicator': 'mean',
                'Manager_Stability_Impact': 'mean',
                'MonthlyIncome': 'mean'
            }).round(2)
            cluster_analysis.to_excel(writer, sheet_name='Cluster Analysis')
        
        print(f"✓ KPI Report exported to: {output_file}")
        return output_file
    
    def export_csv(self, output_file='employee_kpi_data.csv'):
        """Export KPI data to CSV"""
        self.df.to_csv(output_file, index=False)
        print(f"✓ KPI Data exported to: {output_file}")
        return output_file


# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":
    # Initialize analysis
    analyzer = EmployeeKPIAnalysis('Palo Alto Network.csv')
    
    # Generate all KPIs
    kpi_df = analyzer.generate_all_kpis()
    
    # Print summary statistics
    print("\n" + "="*70)
    print("EMPLOYEE KPI SUMMARY STATISTICS")
    print("="*70)
    summary = analyzer.get_summary_statistics()
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    # Display sample of KPI results
    print("\n" + "="*70)
    print("SAMPLE KPI RESULTS (First 10 Employees)")
    print("="*70)
    sample_cols = ['Employe Id', 'Career_Cluster', 'Promotion_Gap_Score',
                  'Retention_Opportunity_Index', 'Training_Need_Indicator',
                  'Intervention_Priority']
    print(kpi_df[sample_cols].head(10).to_string())
    
    # Create visualizations
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS...")
    print("="*70)
    analyzer.create_visualizations()
    
    # Export reports
    print("\n" + "="*70)
    print("EXPORTING REPORTS...")
    print("="*70)
    analyzer.export_kpi_report('Employee_KPI_Report.xlsx')
    analyzer.export_csv('Employee_KPI_Data.csv')
    
    print("\n" + "="*70)
    print("✓ KPI ANALYSIS COMPLETE!")
    print("="*70)
