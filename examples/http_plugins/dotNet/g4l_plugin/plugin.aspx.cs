using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;
using System.Web.Routing;
using System.Reflection;
using System.Text;
using System.Security.Principal;
using System.Configuration;
using System.Web.Script.Serialization;

namespace g4l_plugin
{
    public partial class plugin : System.Web.UI.Page
    {
        private string PLUGIN_USERNAME = ConfigurationManager.AppSettings["plugin_username"];
        private string PLUGIN_PASSWORD = ConfigurationManager.AppSettings["plugin_password"];
        //string BASE_URL = ConfigurationManager.AppSettings["plug_in_base_url"];
        private string context_id;

        public string action = null;

        //Manage Basic HTTP Authentication
        private void check_creadentials(string usename, string password)
        {
            string authInfo = usename + ":" + password;
            string encAuthInfo = "Basic " + Convert.ToBase64String(Encoding.Default.GetBytes(authInfo));

            if ((Request.Headers["Authorization"] == null) || (Request.Headers["Authorization"] != encAuthInfo))
            {
                Response.StatusCode = 401;
                Response.AddHeader("WWW-Authenticate", "Basic realm=\"Please provide correct credentials\"");
                Response.Flush();
            }
        }

        protected void Page_Load(object sender, EventArgs e)
        {
            //Check if credentials are Ok
            check_creadentials(PLUGIN_USERNAME, PLUGIN_PASSWORD);
            action = Page.RouteData.Values["action"].ToString();
            context_id = Request.QueryString["context_id"];

            if (action == "test-plugin")
            {
                //string context_id = Request.QueryString["context_id"];
                Response.ContentType = "application/json";
                Response.Write(services.test_plugin(context_id));
            }
            else if (action == "capabilities")
            {
                Response.ContentType = "application/json";
                Response.Write(services.capabilities(context_id));
            }
            else if (action == "labs")
            {
                Response.ContentType = "application/json";
                Response.Write(services.labs(context_id));
            }
            else if (action == "widgets")
            {
                var laboratory_id = Request.QueryString["laboratory_id"];
                Response.ContentType = "application/json";
                Response.Write(services.getWidgets(laboratory_id));
            }
            else if (action == "widget")
            {
                var widget_name = Request.QueryString["widget_name"];
                var reservation_id = Request.Headers["X-G4L-reservation-id"];
                Response.ContentType = "application/json";
                Response.Write(services.getWidgetUrl(widget_name, reservation_id));
            }
            else if (action == "test-config")
            {
                Response.ContentType = "application/json";
                Response.Write(services.test_config());
            }
            else if (action == "reserve")
            {
                string request = Request.Form["request"];
                Response.ContentType = "application/json";
                Response.Write(services.reserve(request));
            }
            else if (action == "setup")
            {
                string back_url = Request.QueryString["back_url"];
                string baseUrl = Request.Url.Scheme + "://" + Request.Url.Authority + Request.ApplicationPath.TrimEnd('/') + "/";
                Response.ContentType = "application/json";
                Response.Write(services.setup_plugin(baseUrl, back_url, context_id));
            }

            else
            {
                Response.Write("Gateway4labs Plug-in .NET Example. ");
            }

        }



    }
}