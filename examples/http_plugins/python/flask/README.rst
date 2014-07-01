Flask HTTP plug-in example
==========================

Introduction
------------

Let's imagine a theorical remote laboratory which is hosted at:

 - http://localhost:5001/lab/

It is a super cool laboratory. And it requires authentication. 

We need to develop a plug-in to add support to it through gateway4labs. So we need to have other service, for instance:

 - http://localhost:5002/plugin/

That shows that translates the generic HTTP interface to commands that lab understand. Both components could be together (for instance, the lab could support the gateway4labs HTTP interface), but for the sake of clarity we keep them as two independent components.

The first one is the file lab.py

The sample plug-in is plugin.py

