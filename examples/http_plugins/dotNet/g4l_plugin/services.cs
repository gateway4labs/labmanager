using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Windows.Data;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace g4l_plugin
{
    public class services
    {
 //Static methods (e.g., plug-in capabilities or version) 
        //ROUTE: ../plugin/test-plugin
        public static string test_plugin(string context_id) {

            api_version version = new api_version
            {
                valid = true,
                g4l_api_version = "1.0"
            };

            var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
            string jsonString = javaScriptSerializer.Serialize(version);
            return jsonString;
        }

        //ROUTE: ../plugin/capabilities
        public static string capabilities(string context_id) {


            return "Capabilities";
        }
        //ROUTE: ../plugin/labs
        public static string labs(string context_id)
        {
        // This can be retrieved from a database, or by contacting the laboratory
        // in case it manages more than one laboratory.
                      
            lab lab1 = new lab
            {
                laboratory_id = "Sample_lab_1",
                autoload = false,
                name = "Sample Laborytory 1",
                description = "This is an example of laboratory"
            };
            lab lab2 = new lab
            {
                laboratory_id = "Sample_lab_1",
                autoload = true,
                name = "Sample Laborytory 2",
                description = "This is an example of laboratory"
            };

            labsList ListOfLabs = new labsList { labs = new lab[] { lab1, lab2 } };

            var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
            string jsonString = javaScriptSerializer.Serialize(ListOfLabs);
            return jsonString;        
        }

        //ROUTE: ../plugin/widgets
        public static string getWidgets(string laboratory_id)
        {
        // This can be retrieved from a database, or by contacting the laboratory
        // in case it manages more than one laboratory. It will get all widgets of an specific lab given by the laboratory_id parameter
            if (laboratory_id != "Sample_lab_1") //Dummy example, in real life it should query a database
            {
                return "Lab Not found";
            }

            widget widget1 = new widget
            {
                name = "Camera1",
                description = "Left camera"
            };
            widget widget2 = new widget
            {
                name = "Camera2",
                description = "Right camera"
            };

            widgetList wList = new widgetList { widgets = new widget[] { widget1, widget2 } };

            var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
            string jsonString = javaScriptSerializer.Serialize(wList);
            return jsonString; 
           
        }

        //ROUTE: ../plugin/widget
        public static string getWidgetUrl(string widget_name, string reservation_id)
        {
            if (widget_name == "camera1")
            {
                widgetUrl widget1 = new widgetUrl
                {
                    url = "/Camera1/?reservation_id=" + reservation_id, //append lab base url at the begining
                };

                var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
                string jsonString = javaScriptSerializer.Serialize(widget1);
                return jsonString;
            }
            else if (widget_name == "camera2")
            {
                widgetUrl widget2 = new widgetUrl
                {
                    url = "/Camera2/?reservation_id=" + reservation_id, //append lab base url at the begining
                };


                var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
                string jsonString = javaScriptSerializer.Serialize(widget2);
                return jsonString;
            }


            return "widget not found";
        }

        //ROUTE: ../plugin/test-config
        public static string test_config()
        {
            // This method should contact the lab to verify its configuration
            test_report report = new test_report
            {
                valid = true,
                error_messages = "Message goes here"
            };

            var javaScriptSerializer = new System.Web.Script.Serialization.JavaScriptSerializer();
            string jsonString = javaScriptSerializer.Serialize(report);
            return jsonString;             
        }

        //ROUTE: ../plugin/reserve
        public static string reserve(string request)
        {
            var jsonString = request;
            dynamic json = JValue.Parse(jsonString);
            string laboratory_id = json.laboratory_id;
            string username = json.username;
            string institution = json.institution;
          //string general_configuration_str = json.general_configuration_str;
          //string particular_configurations = json.particular_configurations;
          //string request_payload = json.request_payload;
          //string user_properties = json.user_properties;
            
            //Json responses "load_url" and "reservation_id" should be retrieved by querying the lab
            var jsonObject = new JObject();
            jsonObject.Add("load_url", "your.return.url"); 
            jsonObject.Add("reservation_id", "reservation ID");

            return (jsonObject.ToString());
        }

//Setup Application

        //ROUTE: ../plugin/setup
        public static string setup_plugin(string baseUrl, string back_url, string context_id)
        {         
            var response = new JObject();
            //create reservation ID
            Guid id = Guid.NewGuid();
            string reservation_id = id.ToString();
            response.Add("url", baseUrl + "setup/?reservation_id=" + reservation_id);

            //TODO: Store reservations in memory or database

            return response.ToString();
        }
        //ROUTE: ../setup
        public static string setup(string reservation_id)
        {

            return reservation_id;
        }
    }

}