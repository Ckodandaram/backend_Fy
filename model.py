from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import json
from PyPDF2 import PdfWriter, PdfReader, PdfMerger
from PyPDF2.generic import FloatObject
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import date, datetime
import shutil
from tempfile import NamedTemporaryFile
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger()


def convert_dates_in_dict(data):
    """Recursively converts all date and datetime objects in a dictionary to ISO formatted strings."""
    if isinstance(data, dict):
        return {k: convert_dates_in_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_dates_in_dict(i) for i in data]
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    return data


def myModel(file_path,form_number): 
    endpoint = os.getenv("ENDPOINT")
    key = os.getenv("KEY")
    model_id = ""

    if form_number == 1:
        model_id="Form1_Neural"
    elif form_number == 2:
        model_id="Form2_Neural"
    elif form_number == 3:
        model_id="Form3_Neural"
    elif form_number == 4:
        key = os.getenv("KEY2")
        endpoint = os.getenv("ENDPOINT2")
        model_id="voter_neural"
    FORM_NAME = file_path

    document_intelligence_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    with open(FORM_NAME, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id, document=f
        )
    result = poller.result()


    coordinates=[]

    if form_number == 1:
     storage={"Root": {
            "Branch_Name": [],
            "Date": [],
            "Cif_No": [],
            "Name": [],
            "Company_Name": [],
            "Enrollment_Instructions": {
                "Account_Number": [],
                "Atm_Card": {
                    "Avail": [],
                    "No_Need": [],
                    "ATM_Card_Number": []
                },
                "Mobile_Banking": {
                    "Enroll": [],
                    "No_Need": []
                },
                "Online_Banking": {
                    "Enroll": [],
                    "No_Need": [],
                    "User_Id": []
                },
                "Preferred_User_Ids": {
                    "Id1": [],
                    "Id2": [],
                    "Id3": []
                }
            },
            "Maintenance_Requests": {
                "Atm_Card": {
                    "Atm_Card_Number": [],
                    "Request_For_Atm_Card_Replacement":[],
                    "Request_For_Atm_Card_Replacement_With_New_Card_Name": {
                        "Box": [],
                        "Atm_Card_Name": []
                    },
                    "Request_For_Atm_Pin": [],
                    "Unlink_Drop_Account_Numbers": {
                        "Unlink": [],
                        "Account_Numbers": []
                    },
                    "Close_Atm_Account": {
                        "Box":[],
                        "Reason": []
                    }
                
                },
                "Mobile_Banking": {
                    "User_Id": [],
                    "Suspend_Access": [],
                    "Reason": []
                },
                "Online_Banking": {
                    "Username":[],
                    "Request_For_Online_Banking_Login": [],
                    "Request_For_Online_Banking_Transaction_Password": [],
                    "Increase_My_Fund_Transfer": [],
                    "Unlink_Drop_Account_Numbers": {
                        "Unlink": [],
                        "Account_Numbers": []
                    },
                    "Close_Online_Banking_Account": {
                        "Box":[],
                        "Reason": []
                    }
                },
                "Phone_Banking": {
                    "Phone_Banking_Account_Number": [],
                    "Request_For_Phone_Banking_Access_Tpin": [],
                    "Request_For_Phone_Banking_Transaction_Tpin": [],
                    "Unlink_Drop_Account_Numbers": {
                        "Unlink": [],
                        "Account_Numbers": []
                    },
                    "Link_Drop_Account_Number": {
                        "Link": [],
                        "Drop":[],
                        "Account_Numbers": []
                    },
                    "For_Interbank_Fund_Transfers": {
                        "Account_Name": [],
                        "Name_Of_Bank": []
                    }
                },
                "Remarks": []
            },
            "Receiving_Branch": {
                "Received_By_Date": [],
                "Branch_Name": []
            },
            "Maintaining_Branch": {
                "Checked_By_Date": [],
                "Approved_By_Date": []
            },
            "Alternative_Channels_Division": {
                "Received_By_Date": [],
                "Processed_By_Date": [],
                "Checked_By_Date": []
            },
            "Customer's_Acknowledgment": {
                "Atm_Card": {
                    "Issued_By_Date": [],
                    "Received_By_Date": []
                },
                "Atm_Pin": {
                    "Issued_By_Date": [],
                    "Received_By_Date": []
                },
                "Phone_Banking_Tpin": {
                    "Issued_By_Date": [],
                    "Received_By_Date": []
                }
            }
        }
    }
    elif form_number == 2:
      storage={"Root": {
        "Phillippine_Peso": [],
        "Us_Dollar": [],
        "Branch": [],
        "Date_Accomplished": [],
        "Name": [],
        "Gender": {
        "Male": [],
        "Female": []
        },
        "Date_Of_Birth": [],
        "Place_Of_Birth": {
        "Philippines": [],
        "Others": {
            "Box": [],
            "Value": []
        }
        },
        "Nationality": {
        "Filipino": [],
        "Others": {
            "Box": [],
            "Value": []
        }
        },
        "Civil_Status": {
        "Single": [],
        "Married": [],
        "Separated": [],
        "Divorced": [],
        "Widowed": []
        },
        "Name_Of_Spouse": [],
        "Mother_Maiden_Name": [],
        "Mobile_Phone_Number": [],
        "Email_Address": [],
        "Home_Permanent_Address": [],
        "Present_Address": {
        "Same_As_Home_Address": [],
        "Others": []
        },
        "Home_Phone_Number": [],
        "Tin_Sss_Gsis": {
            "Tin":[],
            "Sss":[],
            "Gsis":[],
            "Value": []
        },
        "Source_Of_Fund": {
        "Business": [],
        "Funds_From_Family_Member": [],
        "Inheritance": [],
        "Pension": [],
        "Rent": [],
        "Savings": [],
        "Commission": [],
        "Gifts_And_Donations": [],
        "Interest": [],
        "Profession": [],
        "Salary": [],
        "Winnings": [],
        "Dividend": [],
        "Government_Assistance": [],
        "Investments": [],
        "Remittance": [],
        "Sale_Of_Property": []
        },
        "Employment_Type": {
        "Employed": [],
        "Self_Employed_Business": [],
        "Self_Employed_Professional": [],
        "Retired": [],
        "Not_Applicable": [],
        "Others": {
            "Box": [],
            "Value": []
        }
        },
        "Estimated_Monthly_Transaction": {
        "Below_PHP_20000": [],
        "PHP_20000_To_49999": [],
        "PHP_50000_To_99999": [],
        "PHP_100000_To_499999": [],
        "PHP_500000_To_999000": [],
        "PHP_1000000_And_Above": []
        },
        "Nature_Of_Business": {
            "Admin_Support": [],
            "Financial": [],
            "Professional_Service": [],
            "Agriculture": [],
            "IT": [],
            "Transportation": [],
            "Construction": [],
            "Manufacturing": [],
            "Wholesale": [],
            "Education": [],
            "Mining": [],
            "Others": {
            "Box": [],
            "Value": []
            }
        },
        "Occupation": {
            "Accountant": [],
            "Lawyer": [],
            "Custom_Broker": [],
            "Money_Changer": [],
            "Expatriate": [],
            "Student": [],
            "Jeweler": [],
            "Others": {
            "Box": [],
            "Value": []
            }
        },
        "Business_Name": [],
        "Work_Business_Phone_Number":[],
        "Work_Business_Address": [],
        "Preferred_Mailing_Address": {
        "Home_Permanent_Address": [],
        "Present_Address": []
        },
        "Residency": {
        "Resident": [],
        "ACR_I_Card_No": [],
        "Non_Resident": []
        },
        "Affiliations_With_China_Bank": {
        "I_Am_A_Director": {
            "Yes": [],
            "No": [],
            "Employee_No": []
        },
        "My_Relative_Is_A_Director": {
            "Yes": [],
            "No": [],
            "Name": []
        },
        "I_Am_Related": {
            "Yes": [],
            "No": []
        },
        "Relationship_With_Government_Personnel": {
            "Occupying":[],
            "Relative": [],
            "Association": [],
            "Position": []
            }
        },
        "For_Bank_Use": {
        "Branch_Unit": [],
        "Cif_No": [],
        "Oks_Account_No": [],
        "Atm_Card_No": [],
        "Referred_By": [],
        "Industry_Sub_Class": [],
        "Interviewed_By_Date": [],
        "Sig_Verified_By_Date": [],
        "Approved_By_Date": [],
        "Account_Opened_By_Date": [],
        "Scanned_By_Date": []
        },
        "Account_Opening_Kit": {
        "Atm_Card": [],
        "Atm_Pin": []
        },
        "Foreign_Account_Tax_Information": {
        "Are_You_Us_Citizen": {
            "Yes": [],
            "No": []
        },
        "Do_You_Have_Any_Records_In_Us": {
            "Yes": [],
            "No": []
        }
        },
        "Access_To_Alternative_Channels": {
        "Mobile_Banking": {
            "Enroll": [],
            "No_Need": []
        },
        "Online_Banking": {
            "Enroll": [],
            "No_Need": [],
            "Preferred_User_Id": {
            "1": [],
            "2": [],
            "3": []
            }
        }
        }
     }
    }
    elif form_number == 3:
      storage={"Root": {
        "Atm_Savings": [],
        "Atm_Checking": [],
        "Branch": [],
        "Date_Accomplished": [],
        "Company_Name": [],
        "Access_To_Alternative_Channels": {
        "Mobile_Banking": {
            "Enroll": [],
            "No_Need": []
        },
        "Online_Banking": {
            "Enroll": [],
            "No_Need": [],
            "Preferred_User_Id": {
            "Preferred_User_Id1": [],
            "Preferred_User_Id2": [],
            "Preferred_User_Id3": []
            }
        }
        },
        "For_Bank_Use": {
        "Employee_Cif_No": [],
        "Employer_Cif_No": [],
        "Employee_Account_No": [],
        "Atm_Card_No": [],
        "Referred_By": [],
        "Sig_Verified_By_Date": [],
        "Account_Opened_By_Date": [],
        "Approved_By_Date": [],
        "Scanned_By_Date": []
        },
        "For_Acd_Use": {
        "Received_By_Date": [],
        "Processed_By_Date": [],
        "Checked_By_Date": [],
        "Remarks": []
        },
        "Employee_Information": {
        "Name": [],
        "Gender": {
            "Male": [],
            "Female": []
        },
        "Date_Of_Birth": [],
        "Place_Of_Birth": {
            "Philippines": [],
            "Others": {
            "Box": [],
            "Value": []
            }
        },
        "Nationality": {
            "Filipino": [],  
            "Others": {
            "Box": [],   
            "Value": []    
            }
        },
        "Civil_Status": {
            "Single": [],
            "Married": [],
            "Separated": [],
            "Divorced": [],
            "Widowed": []
        },
        "Name_Of_Spouse": [],
        "Mother_Maiden_Name": [],
        "Home_Phone_Number": [],
        "Home_Permanent_Address": [],
        "Home_Permanent_Address_Zip_Code": [],
        "Present_Address": {
            "Same_As_Home_Address": [],
            "Others": [],
            "Zipcode":[]
            },
        "Mobile_Phone_Number": [],
        "Email_Address": [],
        "Tin_Sss": {
            "Tin":[],
            "Sss":[],
            "Value": []
        },
        "Occupation": {
            "Accountant": [],
            "Custom_Broker": [],
            "Jeweler": [],
            "Lawyer": [],
            "Money_Changer": [],
            "Others": {
            "Box": [],
            "Value": []
            }
        },
        "Employee_Id": [],
        "Date_Hired": [],
        "Gross_Monthly_Income": {
            "Below_PHP_20000": [],
            "PHP_20000_To_49999": [],
            "PHP_50000_To_99999": [],
            "PHP_100000_To_499999": [],
            "PHP_500000_To_999000": [],
            "PHP_1000000_And_Above": []
        },
        "Employer_Nature_Of_Business": {
            "Agriculture_Fishing": [],
            "Admin_Support": [],
            "Construction": [],
            "Education": [],
            "Financial_Insurance": [],
            "It_Communication": [],
            "Manufacturing": [],
            "Mining_Quarrying": [],
            "Professional_Service": [],
            "Transportation_Storage": [],
            "Wholesale_Retail": [],
            "Others": {
            "Box": [],
            "Value": []
            }
        },
        "Work_Business_Address": [],
        "Work_Business_Phone_Number":[],
        "Affiliations_With_China_Bank": {
            "I_Am_A_Director": {
                "Yes": [],
                "No": [],
                "Employee_No": []
            },
            "My_Relative_Is_A_Director": {
                "Yes": [],
                "No": [],
                "Name": [],
                "Relationship": []
            },
            "I_Am_Related": {
                "Yes": [],
                "No": []
            },
            "Relationship_With_Government_Personnel": {
                "Occupying":[],
                "Relative": [],
                "Association": [],
                "Position": []
                }
            },
        "Residency": {
            "Resident": [],
            "Acr_I_Card_No": [],
            "Non_Resident": []
        },
        "Preferred_Mailing_Address": {
            "Home_Permanent_Address": [],
            "Present_Address": [],
            "Work_Business_Address": []
        }
        },
        "Foreign_Account_Tax_Compliance_Act_Information": {
        "Are_You_Us_Citizen": {
            "Yes": [],
            "No": []
        },
        "Do_You_Have_Any_Records_In_Us": {
            "Yes": [],
            "No": []
        }
        }
    
    }
   } 
    elif form_number == 4:
      storage={"Root": {
        "1": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "2": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "3": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "4": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "5": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "6": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "7": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "8": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "9": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        },
        "10": {
            "Name": [],
            "Street": [],
            "City": [],
            "Phonenumber": [],
            "Email": [],
            "Date": []
        }
     }
    }
        
    for document in result.documents:
        for name, field in document.fields.items():
            value=field.value if field.value else field.content
            #print(f"{name}={value} [{field.confidence}]")
            storage[name]=[value,field.confidence]
            if "signature" in name.lower():
                points=field.bounding_regions[0].polygon
                for p in points:
                    coordinates.append((p.x*72,p.y*72))

    # After populating the `storage` dictionary, convert date fields
    storage = convert_dates_in_dict(storage)  # Apply conversion to all date fields in the dictionary

    # Now convert `storage` to JSON
    nested_dict = {}
    for key, value in storage.items():
        keys_list = key.split("|")
        temp_dict = nested_dict

        for k in keys_list[:-1]:
            temp_dict = temp_dict.setdefault(k, {})

        temp_dict[keys_list[-1]] = value

    json_str = json.dumps(nested_dict, indent=4)
    return json_str



def analyze_document(file_path,form_number):
   
    endpoint = os.getenv("ENDPOINT")
    key = os.getenv("KEY")
    model_id = ""

    if form_number == 1:
        model_id="Form1_Template"
    elif form_number == 2:
        model_id="Form2_Template"
    elif form_number == 3:
        model_id="Form3_Templatee"
    elif form_number == 4:
        endpoint = os.getenv("ENDPOINT2")
        key = os.getenv("KEY2")
        model_id="voter_neural"

    document_intelligence_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )
  
    with open(file_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id, document=f
        )
    result = poller.result()

    coordinates = []
    for document in result.documents:
        for name, field in document.fields.items():
            if "signature" in name.lower():
                points = field.bounding_regions[0].polygon
                for p in points:
                    coordinates.append((p.x*72, p.y*72))

   
    return coordinates

def modify_pdf_with_signature(file_path, coordinates):
    try:
        reader = PdfReader(file_path)
        
        page = reader.pages[0]
        original_lower_left = page.cropbox.lower_left
        original_lower_right = page.cropbox.lower_right
        original_upper_left = page.cropbox.upper_left
        original_upper_right = page.cropbox.upper_right

        height_of_pdf = float(original_upper_left[1])
        width_of_pdf = original_lower_right[0]
       

        writer = PdfWriter()
        page.mediabox.upper_left = (float(coordinates[0][0]), height_of_pdf - float(coordinates[0][1]))
        page.mediabox.upper_right = (float(coordinates[1][0]), height_of_pdf - float(coordinates[1][1]))
        page.mediabox.lower_right = (float(coordinates[2][0]), height_of_pdf - float(coordinates[2][1]))
        page.mediabox.lower_left = (float(coordinates[3][0]), height_of_pdf - float(coordinates[3][1]))
        writer.add_page(page)

        # Create a temporary file to store the modified PDF
        with NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file_path = tmp_file.name
            writer.write(tmp_file)
        
        return tmp_file_path
    except Exception as e:
        logger.exception("error coming")
        raise  # Re-raise the exception to propagate it
