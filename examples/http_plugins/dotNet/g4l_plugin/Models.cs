using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace g4l_plugin
{
    public class api_version
    {
        public bool valid { get; set;}
        public string g4l_api_version { get; set;}
    }

    public class capabilities
    {
        public bool labcapabilities { get; set; }
    }

    public class lab
    {
        public string laboratory_id { get; set; }
        public bool autoload { get; set; }
        public string name { get; set; }
        public string description { get; set; }
    }

    public class labsList
    {
        public lab[] labs { get; set; }
    }

    public class widget
    {
        public string name { get; set; }
        public string description { get; set; }
    }

    public class widgetList
    {
        public widget[] widgets { get; set; }
    }

    public class test_report
    {
        public bool valid { get; set; }
        public string error_messages { get; set; }
    }

    public class widgetUrl
    {
        public string url { get; set; }
    }
}