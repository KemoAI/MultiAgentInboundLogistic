""" This code defines a tool to push records to IBL DB """

import sys
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
import asyncio
import requests

# Initialize FastMCP server
mcp = FastMCP("db-server")

@mcp.tool()
async def UpdateDB(record: Dict[str, Any] , agent: str) -> Dict[str, Any]:
    """
    Update the IBL database and confirm back.

    Args:
        record: Record details of dictionary type.

    Returns:
        A dictionary contains a success status and the new record

    """
    
    print('Data ===> ' , record)
    if agent == "LOGISTICS":
        clearingNumber = None
        status = None
        errorMessage = None
        try:
            ## Call API and get r   esponse
            url = "https://bi.tamergroup.com/test/api/integration/create_shipment"

            # Define the request payload (data you want to send)
            payload = {
                        "division_name": record["Division_Name"] ,
                        "organization_name": record["Organization_Name"],
                        "supplier_name": record["Supplier_Name"]
                        }

            # Define headers (for example, JSON content type and an authorization token)
            headers = {
                "Content-Type": "application/json",
                "authorization": "Bearer eyJpdiI6IlB0aS9KbnhuWVIzdmw0enVwbXVjbUE9PSIsInZhbHVlIjoiWXcxb0trRS9KVmplOVZXdnZ3WkxXQXdMSER3anRNT3laTGRQWTYwdDM4UkdBRGRrdE50YXBnSVdPaENUOUNsbDhXR0FaUEcyL2wrcndiOHErcksrY1E9PSIsIm1hYyI6IjY5M2IwMWUzYzQxZGZhMzcwZTNjZThiMjRjMDU0M2VjNTk3NTdkZTcxZTY0NjE4OTEzNzlkZjYxNjJlNDIwNTQiLCJ0YWciOiIifQ==",
                "Accept": "application/json"
                }
 
            # Send the POST request
            response = requests.post(url, json=payload, headers=headers)

            # Check the response
            if response.status_code == 201 and response.json()['message'] == 'Clearing created successfully':
                print(" Request successful!")
                print("Response JSON:", response.json())
                clearingNumber = str(response.json()['data']['clearing_number'])
                status = True
                errorMessage = None

            else:
                print(f" Request failed with status code {response.status_code}")
                print("Response:", response.text)
                errorMessage = response.text
                status = False
                return {"status" : status, "clearingNumber" : None , "data" :errorMessage}
            

            url = "https://bi.tamergroup.com/test/api/integration/update_shipment"
            payload = {
                "clearing_number": clearingNumber,
                "page": "logistics_agent",
                "data": {
                    "AWB": record["AWB/BL"],
                    "AWB_Date": record["AWB/BL Date"],
                    "Forwarder": record["Forwarder"],
                    "Incoterm": record["Incoterm"],
                    "Temperature_Range": record["Product Temperature"],
                    "Packing": record["Packing"],
                    "Shipping_Temp": record["Shipping Temp"],
                    "Gel_Pack_Expiry_Date": record["Gel Pack Expiry Date"],
                    "Handover": record["Handover to Clearance"],
                    "Aggregation": record["Aggregation"],
                    "Notified_FF_date": record["Notified FF Date"],
                    "Green_light_date": record["Green light - Date"],
                    "Shipment_Mode": record["Shipment Mode"],
                    "Logistic_Comment": record["Logistic Comment"],
                    "Remark": record["Remark"],
                    "ASN_Importation_Date": record["ASN Importation Date"]
                }
            }
            # Define headers (for example, JSON content type and an authorization token)
            headers = {
                "Content-Type": "application/json",
                "authorization": "Bearer eyJpdiI6IlB0aS9KbnhuWVIzdmw0enVwbXVjbUE9PSIsInZhbHVlIjoiWXcxb0trRS9KVmplOVZXdnZ3WkxXQXdMSER3anRNT3laTGRQWTYwdDM4UkdBRGRrdE50YXBnSVdPaENUOUNsbDhXR0FaUEcyL2wrcndiOHErcksrY1E9PSIsIm1hYyI6IjY5M2IwMWUzYzQxZGZhMzcwZTNjZThiMjRjMDU0M2VjNTk3NTdkZTcxZTY0NjE4OTEzNzlkZjYxNjJlNDIwNTQiLCJ0YWciOiIifQ==",
                "Accept": "application/json"
                }

            # Send the POST request
            response = requests.post(url, json=payload, headers=headers)
            # Check the response
            if response.status_code == 200 and response.json()['message'] == "logistics_agent data updated successfully":
                status = True
                return {"status" : status,"clearingNumber": clearingNumber , "data" :response.json()}

            
            else:
                print(f" Request failed with status code {response.status_code}")
                print("Response:", response.text)
                errorMessage = response.text
                status = False
                return {"status" : status, "clearingNumber": None ,"data" :errorMessage}
          
        except Exception as e:
            return {"status" : "failed", "clearingNumber": None , "data" :str(e)}
            
        except Exception as e:
            return {"status" : "failed", "clearingNumber": None , "data" :str(e)}
        
    elif agent == "FORWARDER":
        try:
            # Call API
            url = "https://bi.tamergroup.com/test/api/integration/update_shipment"
            payload = {
                "clearing_number": record["Clearing Number"],
                "page": "Freight_Forwarder",
                "data": {
                        "Ship_Readiness_Date": record["Shipment Readiness Date"],
                        "Pick_Up_Date": record["Pick Up Date"],
                        "NO_of_Pallets": record["No. of Pallets"],
                        "NO_Of_Containers": record["No.of Containers"],
                        "Commodity_Description": record["Commodity Description"],
                        "country_Of_origin": record["Country Of Origin (loading_port)"],
                        "Air_Sea_Port": record["AirPort/SeaPort name"],
                        "Shipping_Line_Air_Line": record["Shipping Line/Airline"],
                        "Port_Of_Destination": record["Port Of Destination"],
                        "Actual_ATA_FF": record["Actual ATA - FF"],
                        "Gross_Weight": record["Gross weight (KG)"],
                        "CBM": record["CBM"],
                        "ETD": record["ETD"],
                        "Chargable_Weight": record["Chargable Weight(KG)"],
                        "Freight_Cost": record["Freight Cost"],
                        "Total_Values_Of_Goods": record["Total values of Goods"],
                        "Freight_Invoice_Number": record["Freight Invoice Number"],
                        "ETA": record["ETA"],
                        "comment": record["Freight Comment"]
                }
            }
            # Define headers (for example, JSON content type and an authorization token)
            headers = {
                "Content-Type": "application/json",
                "authorization": "Bearer eyJpdiI6IlB0aS9KbnhuWVIzdmw0enVwbXVjbUE9PSIsInZhbHVlIjoiWXcxb0trRS9KVmplOVZXdnZ3WkxXQXdMSER3anRNT3laTGRQWTYwdDM4UkdBRGRrdE50YXBnSVdPaENUOUNsbDhXR0FaUEcyL2wrcndiOHErcksrY1E9PSIsIm1hYyI6IjY5M2IwMWUzYzQxZGZhMzcwZTNjZThiMjRjMDU0M2VjNTk3NTdkZTcxZTY0NjE4OTEzNzlkZjYxNjJlNDIwNTQiLCJ0YWciOiIifQ==",
                "Accept": "application/json"
                }

            # Send the POST request
            response = requests.post(url, json=payload, headers=headers)
            # Check the response
            if response.status_code == 200 and response.json()['message'] == "logistics_agent data updated successfully":
                status = True
                return {"status" : status, "data" :response.json()}

            
            else:
                print(f" Request failed with status code {response.status_code}")
                print("Response:", response.text)
                errorMessage = response.text
                status = False
                return {"status" : status,"data" :errorMessage}
        except Exception as e:
                return str(e)
        


@mcp.tool()
async def insertClearingNumber(record: Dict[str, Any] , clearingNumber: str ) -> Dict[str, Any]:
    """
    insertClearingNumber in the database and confirm back with full details.

    Args:
        record: Record details of dictionary type.

    Returns:
        A dictionary contains a success status and the new record

    """
    print('Executing insertClearingNumber mcp tool from agent Logistics: ' , 'With Clearing# : ',clearingNumber)
    try:
        # Define the API endpoint
        url = "http://localhost:8080/clearanceInfo?apiKey=COMMAND_CENTER_AI_KEY"

        # Define the request payload (data you want to send)
        payload = {
        "clearingNumber": clearingNumber
        }

        # Define headers (for example, JSON content type and an authorization token)
        headers = {
        "Content-Type": "application/json"
        }

        # Send the POST request
        response = requests.post(url, json=payload, headers=headers)

        # Check the response
        if response.status_code == 200 or response.status_code == 201:
            print(" Request successful!")
            print("Response JSON:", response.json())
            return {"status" : "success", "data" :response.json()}
        else:
            print(f" Request failed with status code {response.status_code}")
            print("Response:", response.text)
            return {"status" : "failed", "data" :response.text}
          


    except Exception as e:
        return {"status" : "failed", "data" :str(e)}
        
           

# Main execution
if __name__ == "__main__":
    mcp.run(transport="stdio")
