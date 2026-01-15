
from backend.app.parsers.gpo_parser import GPOParser
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

# Sample XML content mimicking Get-GPOReport output
XML_CONTENT = """<GPO xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.microsoft.com/GroupPolicy/Settings">
 <Identifier>{11111111-2222-3333-4444-555555555555}</Identifier>
 <Name>Test GPO</Name>
 <Computer>
  <VersionDirectory>1</VersionDirectory>
  <VersionSysvol>1</VersionSysvol>
  <Enabled>true</Enabled>
  <ExtensionData>
   <Extension xmlns:q1="http://www.microsoft.com/GroupPolicy/Settings/Security" xsi:type="q1:SecuritySettings">
    <q1:AccountPolicy>
     <q1:MinimumPasswordLength>
      <q1:Name>Minimum password length</q1:Name>
      <q1:State>Enabled</q1:State>
      <q1:Value>12</q1:Value>
     </q1:MinimumPasswordLength>
    </q1:AccountPolicy>
   </Extension>
   <Extension xmlns:q2="http://www.microsoft.com/GroupPolicy/Settings/Registry" xsi:type="q2:RegistrySettings">
    <q2:Policy>
     <q2:Name>Disable Task Manager</q2:Name>
     <q2:State>Enabled</q2:State>
    </q2:Policy>
   </Extension>
  </ExtensionData>
 </Computer>
 <User>
  <Enabled>true</Enabled>
 </User>
</GPO>"""

def test_parser():
    parser = GPOParser()
    # We use _parse_xml directly to test the string content
    gpos, settings = parser._parse_xml(XML_CONTENT, "test_file.xml")
    
    print(f"GPOs found: {len(gpos)}")
    print(f"Settings found: {len(settings)}")
    
    if len(settings) == 0:
        print("FAIL: No settings found")
    else:
        for s in settings:
            print(f"- {s.name}: {s.state} (Value: {s.value})")

if __name__ == "__main__":
    test_parser()
