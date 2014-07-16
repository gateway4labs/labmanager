using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
//using System.Web.Optimization;
using System.Web.Routing;
using System.Web.Security;
using g4l_plugin;


namespace g4l_plugin
{
    public class Global : HttpApplication
    {
        void Application_Start(object sender, EventArgs e)
        {

            RegisterRoutes(RouteTable.Routes);
           
        }

        void Application_End(object sender, EventArgs e)
        {
            //  Code that runs on application shutdown

        }

        void Application_Error(object sender, EventArgs e)
        {
            // Code that runs when an unhandled error occurs

        }

        static void RegisterRoutes(RouteCollection routes)
        {
            routes.MapPageRoute("About", "About", "~/About.aspx");
            routes.MapPageRoute("setup", "setup", "~/setup.aspx");
            routes.MapPageRoute("plugin", "plugin/{action}", "~/plugin.aspx");
        }        

    }
}
