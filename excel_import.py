"""
Excel Import Module for Litigation Tracker
Handles robust Excel parsing with flexible column mapping
"""
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session

from models import Case, Party, Forum, CaseStatus, AffidavitStatus


# Column name mappings - maps various possible Excel column names to database fields
# Each database field has multiple possible column name variations
COLUMN_MAPPINGS = {
    'case_id': [
        'case id', 'caseid', 'case_id', 'system id', 'systemid', 'id', 'case identifier'
    ],
    'forum': [
        'forum', 'court', 'court type', 'forum type', 'tribunal', 'court/forum'
    ],
    'case_type': [
        'case type', 'casetype', 'case_type', 'type', 'matter type', 'type of case'
    ],
    'case_no': [
        'case no', 'case no.', 'caseno', 'case_no', 'case number', 'casenumber', 
        'case_number', 'writ no', 'petition no', 'appeal no', 'case ref'
    ],
    'connected_case_nos': [
        'connected case', 'connected cases', 'connected case nos', 'connected case no',
        'connected_case_nos', 'related cases', 'linked cases'
    ],
    'is_appeal': [
        'is appeal', 'appeal', 'is_appeal', 'isappeal', 'appeal case', 'whether appeal'
    ],
    'lower_court_case_no': [
        'lower court case no', 'lower court case', 'lower_court_case_no', 
        'original case no', 'lower court ref', 'appealed case no'
    ],
    'lower_court': [
        'lower court', 'lower_court', 'lowercourt', 'original court', 
        'court below', 'appealed from'
    ],
    'lower_court_order_date': [
        'lower court order date', 'lower_court_order_date', 'lc order date',
        'original order date', 'impugned order date'
    ],
    'counsel_name': [
        'counsel', 'counsel name', 'counsel_name', 'counselname', 'advocate',
        'lawyer', 'counsel on record', 'cor', 'attorney'
    ],
    'counsel_contact': [
        'counsel contact', 'counsel_contact', 'contact', 'contact no', 
        'phone', 'mobile', 'counsel phone', 'advocate contact'
    ],
    'asg_engaged': [
        'asg engaged', 'asg_engaged', 'asgengaged', 'asg', 'additional solicitor general'
    ],
    'brief_facts': [
        'brief facts', 'brief_facts', 'brieffacts', 'facts', 'case summary',
        'summary', 'description', 'case details', 'matter details'
    ],
    'last_hearing_date': [
        'last hearing date', 'last_hearing_date', 'lasthearingdate', 
        'previous hearing', 'last date', 'prev hearing date'
    ],
    'next_hearing_date': [
        'next hearing date', 'next_hearing_date', 'nexthearingdate',
        'next date', 'upcoming hearing', 'next hearing', 'scheduled date'
    ],
    'affidavit_status': [
        'affidavit status', 'affidavit_status', 'affidavitstatus',
        'dept affidavit status', 'affidavit'
    ],
    'case_status': [
        'case status', 'case_status', 'casestatus', 'status', 'current status',
        'matter status', 'stage'
    ],
    'final_order_date': [
        'final order date', 'final_order_date', 'finalorderdate',
        'order date', 'judgment date', 'decision date'
    ],
    # Party fields - Petitioners
    'petitioner_1_name': [
        'petitioner', 'petitioner 1', 'petitioner1', 'petitioner_1', 'petitioner name',
        'petitioner 1 name', 'p1', 'p1 name', 'first petitioner', 'appellant',
        'applicant', 'complainant'
    ],
    'petitioner_1_address': [
        'petitioner address', 'petitioner 1 address', 'petitioner_1_address',
        'p1 address', 'petitioner addr', 'appellant address'
    ],
    'petitioner_2_name': [
        'petitioner 2', 'petitioner2', 'petitioner_2', 'p2', 'p2 name',
        'second petitioner', 'petitioner 2 name'
    ],
    'petitioner_2_address': [
        'petitioner 2 address', 'petitioner_2_address', 'p2 address'
    ],
    'petitioner_3_name': [
        'petitioner 3', 'petitioner3', 'petitioner_3', 'p3', 'p3 name'
    ],
    'petitioner_3_address': [
        'petitioner 3 address', 'petitioner_3_address', 'p3 address'
    ],
    # Party fields - Respondents
    'respondent_1_name': [
        'respondent', 'respondent 1', 'respondent1', 'respondent_1', 'respondent name',
        'respondent 1 name', 'r1', 'r1 name', 'first respondent', 'defendant',
        'opposite party', 'op'
    ],
    'respondent_1_address': [
        'respondent address', 'respondent 1 address', 'respondent_1_address',
        'r1 address', 'respondent addr', 'defendant address'
    ],
    'respondent_2_name': [
        'respondent 2', 'respondent2', 'respondent_2', 'r2', 'r2 name',
        'second respondent', 'respondent 2 name'
    ],
    'respondent_2_address': [
        'respondent 2 address', 'respondent_2_address', 'r2 address'
    ],
    'respondent_3_name': [
        'respondent 3', 'respondent3', 'respondent_3', 'r3', 'r3 name'
    ],
    'respondent_3_address': [
        'respondent 3 address', 'respondent_3_address', 'r3 address'
    ],
}

# Valid forum values mapping
FORUM_MAPPINGS = {
    'cat': Forum.CAT.value,
    'central administrative tribunal': Forum.CAT.value,
    'hc': Forum.HC.value,
    'high court': Forum.HC.value,
    'sc': Forum.SC.value,
    'supreme court': Forum.SC.value,
    'other': Forum.OTHER.value,
    'other tribunals': Forum.OTHER.value,
    'tribunal': Forum.OTHER.value,
    'ngt': Forum.OTHER.value,
    'nclt': Forum.OTHER.value,
    'itat': Forum.OTHER.value,
}

# Valid status mappings
STATUS_MAPPINGS = {
    'filed': CaseStatus.FILED.value,
    'new': CaseStatus.FILED.value,
    'admission': CaseStatus.ADMISSION.value,
    'admitted': CaseStatus.ADMISSION.value,
    'hearing': CaseStatus.HEARING.value,
    'in hearing': CaseStatus.HEARING.value,
    'under hearing': CaseStatus.HEARING.value,
    'dismissed': CaseStatus.DISMISSED.value,
    'closed': CaseStatus.DISMISSED.value,
    'adjourned': CaseStatus.ADJOURNED.value,
    'reserved': CaseStatus.RESERVED.value,
    'reserved for judgment': CaseStatus.RESERVED.value,
    'allowed': CaseStatus.ALLOWED.value,
    'disposed': CaseStatus.ALLOWED.value,
    'decided': CaseStatus.ALLOWED.value,
}

# Affidavit status mappings
AFFIDAVIT_MAPPINGS = {
    'filed': AffidavitStatus.FILED.value,
    'pwc submitted': AffidavitStatus.PWC_SUBMITTED_SC.value,
    'pwc submitted to sc': AffidavitStatus.PWC_SUBMITTED_SC.value,
    'pwc pending': AffidavitStatus.PWC_PENDING.value,
    'pending': AffidavitStatus.PWC_PENDING.value,
    'affidavit submitted': AffidavitStatus.AFFIDAVIT_SUBMITTED_SC.value,
    'affidavit submitted to sc': AffidavitStatus.AFFIDAVIT_SUBMITTED_SC.value,
    'draft received': AffidavitStatus.DRAFT_RECEIVED.value,
    'draft affidavit received': AffidavitStatus.DRAFT_RECEIVED.value,
    'sent for vetting': AffidavitStatus.SENT_VETTING.value,
    'vetting': AffidavitStatus.SENT_VETTING.value,
}


def normalize_column_name(col_name: str) -> str:
    """Normalize column name for matching"""
    if not isinstance(col_name, str):
        return str(col_name).lower().strip()
    # Remove special characters, convert to lowercase, strip whitespace
    normalized = re.sub(r'[^a-z0-9\s]', '', col_name.lower().strip())
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def map_columns(excel_columns: List[str]) -> Dict[str, str]:
    """
    Map Excel columns to database fields
    Returns: Dict mapping database field names to Excel column names
    """
    column_map = {}
    normalized_excel_cols = {normalize_column_name(col): col for col in excel_columns}
    
    for db_field, possible_names in COLUMN_MAPPINGS.items():
        for possible_name in possible_names:
            normalized_possible = normalize_column_name(possible_name)
            if normalized_possible in normalized_excel_cols:
                column_map[db_field] = normalized_excel_cols[normalized_possible]
                break
    
    return column_map


def parse_boolean(value: Any) -> bool:
    """Parse various boolean representations"""
    if isinstance(value, bool):
        return value
    if pd.isna(value) or value is None:
        return False
    str_val = str(value).lower().strip()
    return str_val in ('yes', 'y', 'true', '1', 'on', 'checked', 'x')


def parse_date(value: Any) -> Optional[date]:
    """Parse various date formats"""
    if pd.isna(value) or value is None:
        return None
    
    if isinstance(value, (datetime, date)):
        return value.date() if isinstance(value, datetime) else value
    
    if isinstance(value, pd.Timestamp):
        return value.date()
    
    str_val = str(value).strip()
    if not str_val or str_val.lower() in ('nat', 'none', 'null', '-', 'na', 'n/a'):
        return None
    
    # Try various date formats
    date_formats = [
        '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y',
        '%d-%b-%Y', '%d %b %Y', '%d-%B-%Y', '%d %B %Y',
        '%Y/%m/%d', '%d.%m.%Y', '%Y.%m.%d'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str_val, fmt).date()
        except ValueError:
            continue
    
    return None


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def parse_forum(value: Any, strict: bool = True) -> str:
    """Parse and validate forum value"""
    if pd.isna(value) or value is None or str(value).strip() == '':
        if strict:
            raise ValidationError("Forum is required")
        return Forum.OTHER.value
    
    str_val = normalize_column_name(str(value))
    result = FORUM_MAPPINGS.get(str_val)
    
    if result is None:
        if strict:
            valid_values = list(set(FORUM_MAPPINGS.values()))
            raise ValidationError(f"Invalid forum '{value}'. Valid values: {', '.join(valid_values)}")
        return Forum.OTHER.value
    
    return result


def parse_status(value: Any, strict: bool = True) -> str:
    """Parse and validate case status"""
    if pd.isna(value) or value is None or str(value).strip() == '':
        return CaseStatus.FILED.value  # Default is acceptable
    
    str_val = normalize_column_name(str(value))
    result = STATUS_MAPPINGS.get(str_val)
    
    if result is None:
        if strict:
            valid_values = list(set(STATUS_MAPPINGS.values()))
            raise ValidationError(f"Invalid case status '{value}'. Valid values: {', '.join(valid_values)}")
        return CaseStatus.FILED.value
    
    return result


def parse_affidavit_status(value: Any, strict: bool = True) -> Optional[str]:
    """Parse and validate affidavit status"""
    if pd.isna(value) or value is None or str(value).strip() == '':
        return None
    
    str_val = normalize_column_name(str(value))
    result = AFFIDAVIT_MAPPINGS.get(str_val)
    
    if result is None and strict:
        valid_values = list(set(AFFIDAVIT_MAPPINGS.values()))
        raise ValidationError(f"Invalid affidavit status '{value}'. Valid values: {', '.join(valid_values)}")
    
    return result


def parse_date_strict(value: Any, field_name: str) -> Optional[date]:
    """Parse date with strict validation"""
    result = parse_date(value)
    if result is None and value is not None and not pd.isna(value):
        str_val = str(value).strip()
        if str_val and str_val.lower() not in ('nat', 'none', 'null', '-', 'na', 'n/a', ''):
            raise ValidationError(f"Invalid date format for '{field_name}': '{value}'. Use formats like YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY")
    return result


def clean_string(value: Any) -> Optional[str]:
    """Clean and return string value"""
    if pd.isna(value) or value is None:
        return None
    str_val = str(value).strip()
    return str_val if str_val and str_val.lower() not in ('nan', 'none', 'null', '-', 'na', 'n/a') else None


def generate_case_id(db: Session) -> str:
    """Generate case ID in YYYY001 format"""
    year = datetime.now().year
    prefix = str(year)
    
    last_case = db.query(Case).filter(
        Case.case_id.like(f"{prefix}%")
    ).order_by(Case.case_id.desc()).first()
    
    if last_case:
        last_num = int(last_case.case_id[4:])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f"{prefix}{new_num:03d}"


def process_excel_file(
    file_content: bytes,
    db: Session,
    user_id: int,
    strict_mode: bool = True
) -> Tuple[int, int, List[str]]:
    """
    Process Excel file and import cases into database
    
    Args:
        file_content: Excel file content as bytes
        db: Database session
        user_id: ID of user performing import
        strict_mode: If True, reject rows with invalid values. If False, use defaults.
    
    Returns:
        Tuple of (success_count, error_count, error_messages)
    """
    errors = []
    success_count = 0
    error_count = 0
    
    try:
        # Read Excel file
        df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        
        if df.empty:
            return 0, 0, ["Excel file is empty"]
        
        # Map columns
        column_map = map_columns(df.columns.tolist())
        
        if not column_map:
            return 0, 0, ["No recognizable columns found in the Excel file. Please ensure column headers match expected names."]
        
        # Check for required columns in strict mode
        if strict_mode and 'forum' not in column_map:
            return 0, 0, ["Required column 'Forum' not found. Please add a Forum column to your Excel file."]
        
        # Process each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # Excel row number (1-indexed + header)
            row_errors = []
            
            try:
                # Extract case data
                case_data = {}
                
                # Get forum (required)
                if 'forum' in column_map:
                    try:
                        case_data['forum'] = parse_forum(row.get(column_map['forum']), strict=strict_mode)
                    except ValidationError as e:
                        row_errors.append(str(e))
                        if strict_mode:
                            raise
                        case_data['forum'] = Forum.OTHER.value
                else:
                    if strict_mode:
                        row_errors.append("Forum is required")
                        raise ValidationError("Forum is required")
                    case_data['forum'] = Forum.OTHER.value
                
                # Map text fields (no validation needed)
                text_fields = ['case_type', 'case_no', 'connected_case_nos', 
                              'lower_court_case_no', 'lower_court', 'counsel_name', 
                              'counsel_contact', 'brief_facts']
                
                for field in text_fields:
                    if field in column_map:
                        case_data[field] = clean_string(row.get(column_map[field]))
                
                # Map boolean fields
                bool_fields = ['is_appeal', 'asg_engaged']
                for field in bool_fields:
                    if field in column_map:
                        case_data[field] = parse_boolean(row.get(column_map[field]))
                
                # Map date fields with strict validation
                date_fields = {
                    'lower_court_order_date': 'Lower Court Order Date',
                    'last_hearing_date': 'Last Hearing Date',
                    'next_hearing_date': 'Next Hearing Date',
                    'final_order_date': 'Final Order Date'
                }
                
                for field, display_name in date_fields.items():
                    if field in column_map:
                        try:
                            if strict_mode:
                                case_data[field] = parse_date_strict(row.get(column_map[field]), display_name)
                            else:
                                case_data[field] = parse_date(row.get(column_map[field]))
                        except ValidationError as e:
                            row_errors.append(str(e))
                            if strict_mode:
                                raise
                            case_data[field] = None
                
                # Handle case status with validation
                if 'case_status' in column_map:
                    try:
                        case_data['case_status'] = parse_status(row.get(column_map['case_status']), strict=strict_mode)
                    except ValidationError as e:
                        row_errors.append(str(e))
                        if strict_mode:
                            raise
                        case_data['case_status'] = CaseStatus.FILED.value
                else:
                    case_data['case_status'] = CaseStatus.FILED.value
                
                # Handle affidavit status with validation
                if 'affidavit_status' in column_map:
                    try:
                        case_data['affidavit_status'] = parse_affidavit_status(
                            row.get(column_map['affidavit_status']), strict=strict_mode
                        )
                    except ValidationError as e:
                        row_errors.append(str(e))
                        if strict_mode:
                            raise
                        case_data['affidavit_status'] = None
                
                # Validate: At least case_no OR one petitioner should be present
                has_case_no = case_data.get('case_no') is not None
                has_petitioner = False
                
                for i in range(1, 4):
                    name_field = f'petitioner_{i}_name'
                    if name_field in column_map:
                        name = clean_string(row.get(column_map[name_field]))
                        if name:
                            has_petitioner = True
                            break
                
                if strict_mode and not has_case_no and not has_petitioner:
                    raise ValidationError("Either Case No. or at least one Petitioner name is required")
                
                # Generate case ID
                case_data['case_id'] = generate_case_id(db)
                case_data['created_by'] = user_id
                case_data['updated_by'] = user_id
                
                # Create case
                case = Case(**case_data)
                db.add(case)
                db.flush()  # Get the case ID
                
                # Process petitioners
                for i in range(1, 4):
                    name_field = f'petitioner_{i}_name'
                    addr_field = f'petitioner_{i}_address'
                    
                    if name_field in column_map:
                        name = clean_string(row.get(column_map[name_field]))
                        if name:
                            address = None
                            if addr_field in column_map:
                                address = clean_string(row.get(column_map[addr_field]))
                            
                            party = Party(
                                case_id=case.id,
                                party_type='petitioner',
                                party_number=i,
                                name=name,
                                address=address
                            )
                            db.add(party)
                
                # Process respondents
                for i in range(1, 4):
                    name_field = f'respondent_{i}_name'
                    addr_field = f'respondent_{i}_address'
                    
                    if name_field in column_map:
                        name = clean_string(row.get(column_map[name_field]))
                        if name:
                            address = None
                            if addr_field in column_map:
                                address = clean_string(row.get(column_map[addr_field]))
                            
                            party = Party(
                                case_id=case.id,
                                party_type='respondent',
                                party_number=i,
                                name=name,
                                address=address
                            )
                            db.add(party)
                
                success_count += 1
                
            except (ValidationError, Exception) as e:
                error_count += 1
                error_msg = str(e) if isinstance(e, ValidationError) else f"Unexpected error: {str(e)}"
                errors.append(f"Row {row_num}: {error_msg}")
                db.rollback()  # Rollback this row's changes
                continue
        
        # Commit all successful changes
        db.commit()
        
    except Exception as e:
        db.rollback()
        return 0, 1, [f"Failed to process Excel file: {str(e)}"]
    
    return success_count, error_count, errors


def get_sample_template() -> pd.DataFrame:
    """Generate a sample Excel template with expected columns"""
    columns = [
        'Forum', 'Case Type', 'Case No.', 'Connected Case Nos', 'Is Appeal',
        'Lower Court', 'Lower Court Case No', 'Lower Court Order Date',
        'Counsel Name', 'Counsel Contact', 'ASG Engaged',
        'Brief Facts', 'Last Hearing Date', 'Next Hearing Date',
        'Affidavit Status', 'Case Status',
        'Petitioner 1 Name', 'Petitioner 1 Address',
        'Petitioner 2 Name', 'Petitioner 2 Address',
        'Respondent 1 Name', 'Respondent 1 Address',
        'Respondent 2 Name', 'Respondent 2 Address',
    ]
    
    sample_data = [{
        'Forum': 'HC',
        'Case Type': 'Writ Petition',
        'Case No.': 'WP(C) 1234/2024',
        'Connected Case Nos': '',
        'Is Appeal': 'No',
        'Lower Court': '',
        'Lower Court Case No': '',
        'Lower Court Order Date': '',
        'Counsel Name': 'John Doe',
        'Counsel Contact': '9876543210',
        'ASG Engaged': 'No',
        'Brief Facts': 'Sample case facts...',
        'Last Hearing Date': '2024-01-15',
        'Next Hearing Date': '2024-02-20',
        'Affidavit Status': 'Filed',
        'Case Status': 'Hearing',
        'Petitioner 1 Name': 'ABC Corporation',
        'Petitioner 1 Address': '123 Main Street, City',
        'Petitioner 2 Name': '',
        'Petitioner 2 Address': '',
        'Respondent 1 Name': 'Union of India',
        'Respondent 1 Address': 'Ministry of Law, New Delhi',
        'Respondent 2 Name': '',
        'Respondent 2 Address': '',
    }]
    
    return pd.DataFrame(sample_data, columns=columns)

