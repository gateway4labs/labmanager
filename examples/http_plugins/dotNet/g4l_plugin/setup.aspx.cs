using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.UI;
using System.Web.UI.WebControls;

namespace g4l_plugin
{
    public partial class setup : System.Web.UI.Page
    {

        protected void Page_Load(object sender, EventArgs e)
        {
            string reservation_id = Request.QueryString["reservation_id"];
            //Response.Write(WebMethods.setup(reservation_id));
        }

    }
}