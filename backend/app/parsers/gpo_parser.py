# =============================================================================
# GPO Parser - Supports HTML, HTM, XML formats from AD GPO exports
# =============================================================================

import re
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from lxml import etree

from backend.app.models.gpo import (
    GPOInfo, GPOLink, PolicySetting, PolicyState
)

logger = logging.getLogger(__name__)


class GPOParser:
    """
    Parser for Active Directory Group Policy Object exports.
    
    Supports:
    - HTML/HTM reports from Get-GPOReport -ReportType HTML
    - XML reports from Get-GPOReport -ReportType XML
    - gpresult /H output
    - gpresult /X output
    """
    
    def __init__(self):
        self.gpos: list[GPOInfo] = []
        self.settings: list[PolicySetting] = []
    
    def parse_file(self, file_path: Path) -> tuple[list[GPOInfo], list[PolicySetting]]:
        """
        Parse a GPO export file and extract GPO info and settings.
        
        Args:
            file_path: Path to the GPO export file
            
        Returns:
            Tuple of (list of GPOInfo, list of PolicySetting)
        """
        suffix = file_path.suffix.lower()
        
        # Detect encoding by checking BOM or file signature
        raw_bytes = file_path.read_bytes()
        encoding = 'utf-8'
        
        # Check for BOM markers
        if raw_bytes[:2] == b'\xff\xfe':
            # UTF-16 LE BOM
            encoding = 'utf-16-le'
            logger.debug("Detected UTF-16LE encoding (BOM)")
        elif raw_bytes[:2] == b'\xfe\xff':
            # UTF-16 BE BOM
            encoding = 'utf-16-be'
            logger.debug("Detected UTF-16BE encoding (BOM)")
        elif raw_bytes[:3] == b'\xef\xbb\xbf':
            # UTF-8 BOM
            encoding = 'utf-8'
            logger.debug("Detected UTF-8 encoding (BOM)")
        else:
            # No BOM, try to detect from content
            # Check if it looks like UTF-16 (many null bytes in ASCII range)
            if len(raw_bytes) > 100:
                null_count = raw_bytes[:100].count(b'\x00')
                if null_count > 20:  # Likely UTF-16
                    encoding = 'utf-16-le'
                    logger.debug("Detected UTF-16LE encoding (heuristic)")
        
        try:
            content = raw_bytes.decode(encoding)
        except Exception as e:
            logger.warning(f"Failed to decode with {encoding}, falling back to UTF-8 with error replacement: {e}")
            content = raw_bytes.decode('utf-8', errors='replace')
        
        if not content or len(content) < 100:
            logger.error(f"Failed to read file {file_path} properly")
            return [], []
        
        if suffix in ['.html', '.htm']:
            return self._parse_html(content, str(file_path))
        elif suffix == '.xml':
            return self._parse_xml(content, str(file_path))
        else:
            logger.warning(f"Unsupported file format: {suffix}")
            return [], []
    
    def parse_content(self, content: str, filename: str, content_type: str) -> tuple[list[GPOInfo], list[PolicySetting]]:
        """
        Parse GPO content from uploaded data.
        
        Args:
            content: File content as string
            filename: Original filename
            content_type: MIME type or extension hint
            
        Returns:
            Tuple of (list of GPOInfo, list of PolicySetting)
        """
        if 'html' in content_type.lower() or filename.lower().endswith(('.html', '.htm')):
            return self._parse_html(content, filename)
        elif 'xml' in content_type.lower() or filename.lower().endswith('.xml'):
            return self._parse_xml(content, filename)
        else:
            # Try to detect format from content
            if content.strip().startswith('<?xml') or content.strip().startswith('<'):
                if '<html' in content.lower() or '<!doctype html' in content.lower():
                    return self._parse_html(content, filename)
                return self._parse_xml(content, filename)
            return [], []
    
    def _parse_html(self, content: str, source_file: str) -> tuple[list[GPOInfo], list[PolicySetting]]:
        """Parse HTML/HTM format GPO report."""
        soup = BeautifulSoup(content, 'html5lib')
        gpos = []
        settings = []
        
        # Try to extract GPO name from title or header
        gpo_name = self._extract_gpo_name_html(soup, source_file)
        gpo_id = str(uuid.uuid4())
        
        # Look for GPO metadata table
        gpo_info = GPOInfo(
            id=gpo_id,
            name=gpo_name,
            source_file=source_file
        )
        
        # Extract metadata from various HTML structures
        self._extract_metadata_html(soup, gpo_info)
        # Update ID in case it was found in metadata
        gpo_id = gpo_info.id
        
        gpos.append(gpo_info)
        
        # Extract policy settings from tables
        settings.extend(self._extract_settings_html(soup, gpo_id, gpo_name))
        
        logger.info(f"Parsed HTML file '{source_file}': {len(gpos)} GPO(s), {len(settings)} setting(s)")
        return gpos, settings
    
    def _extract_gpo_name_html(self, soup: BeautifulSoup, source_file: str) -> str:
        """Extract GPO name from HTML content."""
        # Try title tag
        title = soup.find('title')
        if title and title.string:
            title_text = title.string.strip()
            # Common patterns: "Group Policy Report - GPO Name" or just "GPO Name"
            if ' - ' in title_text:
                return title_text.split(' - ')[-1].strip()
            return title_text
        
        # Try h1 or h2 headers
        for header in soup.find_all(['h1', 'h2', 'h3']):
            text = header.get_text(strip=True)
            if text and 'gpo' not in text.lower() or len(text) > 3:
                # Skip generic headers like "GPO Report"
                if text.lower() not in ['group policy report', 'gpo report', 'policy report']:
                    return text
        
        # Try to find name in specific table cells
        for td in soup.find_all('td'):
            if td.get_text(strip=True).lower() == 'name:':
                next_td = td.find_next_sibling('td')
                if next_td:
                    return next_td.get_text(strip=True)
        
        # Fallback to filename
        return Path(source_file).stem
    
    def _extract_metadata_html(self, soup: BeautifulSoup, gpo_info: GPOInfo) -> None:
        """Extract GPO metadata from HTML tables."""
        # Look for metadata patterns in tables
        metadata_patterns = {
            'domain': ['domain', 'domain name'],
            'created': ['created', 'creation time', 'created time'],
            'modified': ['modified', 'last modified', 'modified time'],
            'owner': ['owner', 'gpo owner'],
            'guid': ['unique id', 'guid', 'gpo guid', 'unique identifier']
        }
        
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower().rstrip(':')
                value = cells[1].get_text(strip=True)
                
                for field, patterns in metadata_patterns.items():
                    if any(p in label for p in patterns):
                        if field == 'domain':
                            gpo_info.domain = value
                        elif field == 'created':
                            gpo_info.created = self._parse_datetime(value)
                        elif field == 'modified':
                            gpo_info.modified = self._parse_datetime(value)
                        elif field == 'owner':
                            gpo_info.owner = value
                        elif field == 'guid' and value:
                            gpo_info.id = value
        
        # Extract links (Links to Site, Domain, OU)
        self._extract_links_html(soup, gpo_info)

    def _extract_links_html(self, soup: BeautifulSoup, gpo_info: GPOInfo) -> None:
        """Extract GPO links (SOMs) from HTML tables."""
        # Find the "Links" section or table
        # Structure varies, but often under a "Links" header or div
        
        # Method 1: Look for table with headers "Location", "Enforced", "Link Enabled"
        for table in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if 'location' in headers and ('enforced' in headers or 'link enabled' in headers):
                # This is likely the links table
                rows = table.find_all('tr')[1:] # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Map headers to indices
                        loc_idx = -1
                        enforced_idx = -1
                        enabled_idx = -1
                        
                        for i, h in enumerate(headers):
                            if 'location' in h: loc_idx = i
                            elif 'enforced' in h: enforced_idx = i
                            elif 'link enabled' in h or 'enabled' in h: enabled_idx = i
                        
                        if loc_idx != -1:
                            location = cells[loc_idx].get_text(strip=True)
                            enforced = False
                            enabled = True
                            
                            if enforced_idx != -1:
                                enforced_text = cells[enforced_idx].get_text(strip=True).lower()
                                enforced = enforced_text in ['yes', 'true', 'enforced']
                                
                            if enabled_idx != -1:
                                enabled_text = cells[enabled_idx].get_text(strip=True).lower()
                                enabled = enabled_text in ['yes', 'true', 'enabled']
                            
                            if location:
                                gpo_info.links.append(GPOLink(
                                    location=location,
                                    enforced=enforced,
                                    enabled=enabled
                                ))
    
    def _extract_settings_html(self, soup: BeautifulSoup, gpo_id: str, gpo_name: str) -> list[PolicySetting]:
        """Extract policy settings from HTML tables and div-based structures."""
        settings = []
        
        # First, try to parse Get-GPOReport div-based structure
        div_settings = self._extract_settings_from_divs(soup, gpo_id, gpo_name)
        if div_settings:
            logger.info(f"Found {len(div_settings)} settings using div-based parsing")
            settings.extend(div_settings)
        
        # If no div-based settings found, fall back to table-based parsing
        if not div_settings:
            logger.info("No div-based settings found, trying table-based parsing")
            table_settings = self._extract_settings_from_tables(soup, gpo_id, gpo_name)
            settings.extend(table_settings)
        
        return settings
    
    def _extract_settings_from_divs(self, soup: BeautifulSoup, gpo_id: str, gpo_name: str) -> list[PolicySetting]:
        """Extract settings from Get-GPOReport HTML div-based structure.
        
        Handles the structure:
        User/Computer Configuration (Enabled)
          -> Preferences
             -> Windows Settings
                -> Registry
                   -> Collection: ...
                      -> Registry item: <name>
        """
        settings = []
        current_scope = "Computer"
        
        # Find Computer and User Configuration sections
        for config_div in soup.find_all('div', class_='he0_expanded'):
            span = config_div.find('span', class_='sectionTitle')
            if not span:
                continue
                
            config_text = span.get_text(strip=True)
            
            # Determine scope from section title
            if 'computer configuration' in config_text.lower():
                current_scope = "Computer"
            elif 'user configuration' in config_text.lower():
                current_scope = "User"
            else:
                continue
            
            logger.debug(f"Processing {current_scope} Configuration section")
            
            # Find all Registry item divs within this configuration
            # Look for divs with class he4 (registry items are at this level)
            container = config_div.find_next_sibling('div', class_='container')
            if not container:
                continue
            
            # Build category path by traversing the hierarchy
            registry_items = container.find_all('div', class_='he4')
            
            for item_div in registry_items:
                item_span = item_div.find('span', class_='sectionTitle')
                if not item_span:
                    continue
                
                item_title = item_span.get_text(strip=True)
                
                # Check if this is a registry item
                if item_title.startswith('Registry item:'):
                    # Extract setting name from title
                    setting_name = item_title.replace('Registry item:', '').strip()
                    
                    # Find the General section with the properties table
                    item_container = item_div.find_next_sibling('div', class_='container')
                    if not item_container:
                        continue
                    
                    # Extract registry details from the properties table
                    setting = self._parse_registry_item(
                        item_container, setting_name, gpo_id, gpo_name, current_scope
                    )
                    
                    if setting:
                        settings.append(setting)
        
        return settings
    
    def _parse_registry_item(
        self, 
        container, 
        setting_name: str, 
        gpo_id: str, 
        gpo_name: str, 
        scope: str
    ) -> Optional[PolicySetting]:
        """Parse a registry item from Get-GPOReport HTML structure.
        
        Extracts:
        - Action (Update/Create/Delete/Replace) -> determines state
        - Key path
        - Value name
        - Value type
        - Value data
        """
        # Find the General section
        general_div = container.find('div', class_='he4h')
        if not general_div:
            return None
        
        general_container = general_div.find_next_sibling('div', class_='container')
        if not general_container:
            return None
        
        # Find the properties table
        tables = general_container.find_all('table')
        if not tables:
            return None
        
        # Extract data from table rows
        action = None
        key_path = None
        value_name = None
        value_type = None
        value_data = None
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if label == 'action':
                        action = value
                    elif label == 'key path':
                        key_path = value
                    elif label == 'value name':
                        value_name = value
                    elif label == 'value type':
                        value_type = value
                    elif label == 'value data':
                        value_data = value
        
        # Determine state from action
        state = PolicyState.NOT_CONFIGURED
        if action:
            action_lower = action.lower()
            if action_lower in ['update', 'create', 'replace']:
                state = PolicyState.ENABLED
            elif action_lower == 'delete':
                state = PolicyState.DISABLED
        
        # Build category from key path
        category = "Registry"
        if key_path:
            # Use the first part of the key path as category
            parts = key_path.split('\\')
            if len(parts) > 1:
                category = f"Registry/{parts[0]}"
        
        # Build full setting name including value name if available
        full_name = setting_name
        if value_name and value_name != setting_name:
            full_name = f"{setting_name}/{value_name}"
        
        # Format value with type if available
        formatted_value = value_data
        if value_type and value_data:
            formatted_value = f"{value_data} ({value_type})"
        
        return PolicySetting(
            gpo_id=gpo_id,
            gpo_name=gpo_name,
            category=category,
            name=full_name,
            state=state,
            value=formatted_value,
            registry_path=key_path,
            registry_value=value_name,
            scope=scope
        )
    
    def _extract_settings_from_tables(self, soup: BeautifulSoup, gpo_id: str, gpo_name: str) -> list[PolicySetting]:
        """Extract policy settings from HTML tables (legacy parsing method)."""
        settings = []
        current_category = "General"
        current_scope = "Computer"
        
        # Track section headers for category
        for element in soup.find_all(['h2', 'h3', 'h4', 'table', 'div']):
            if element.name in ['h2', 'h3', 'h4']:
                header_text = element.get_text(strip=True)
                # Detect scope from headers
                if 'computer' in header_text.lower():
                    current_scope = "Computer"
                elif 'user' in header_text.lower():
                    current_scope = "User"
                # Update category from section headers
                if header_text and len(header_text) < 100:
                    current_category = header_text
            
            elif element.name == 'table':
                # Parse table rows for settings
                rows = element.find_all('tr')
                headers = []
                
                for row in rows:
                    header_cells = row.find_all('th')
                    if header_cells:
                        headers = [h.get_text(strip=True).lower() for h in header_cells]
                        continue
                    
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        setting = self._parse_setting_row(
                            cells, headers, gpo_id, gpo_name, 
                            current_category, current_scope
                        )
                        if setting:
                            settings.append(setting)
            
            elif element.name == 'div':
                # Check for category indicators in divs
                class_names = ' '.join(element.get('class', []))
                if 'category' in class_names.lower() or 'section' in class_names.lower():
                    div_text = element.get_text(strip=True)[:100]
                    if div_text:
                        current_category = div_text
        
        return settings
    
    def _parse_setting_row(
        self, 
        cells: list, 
        headers: list, 
        gpo_id: str, 
        gpo_name: str,
        category: str, 
        scope: str
    ) -> Optional[PolicySetting]:
        """Parse a table row as a policy setting.
        
        Handles multiple Microsoft GPO HTML formats:
        1. Policy | State | Setting (3 columns)
        2. Policy | Setting (2 columns, state extracted from value)
        """
        if len(cells) < 2:
            return None
        
        cell_texts = [c.get_text(strip=True) for c in cells]
        
        # Skip empty or header-like rows
        if not any(cell_texts) or all(t.lower() in ['policy', 'setting', 'state', 'value'] for t in cell_texts if t):
            return None
        
        # Determine columns based on headers or position
        setting_name = ""
        state = PolicyState.NOT_CONFIGURED
        value = None
        
        # Normalize headers for comparison
        headers_lower = [h.lower() if h else '' for h in headers]
        
        if headers:
            # Find column indices by header name
            policy_idx = -1
            state_idx = -1
            value_idx = -1
            
            for i, header in enumerate(headers_lower):
                if 'policy' in header or 'name' in header:
                    policy_idx = i
                elif 'state' in header or 'status' in header:
                    state_idx = i
                elif 'setting' in header or 'value' in header or 'data' in header:
                    value_idx = i
            
            # Extract values based on found indices
            if policy_idx >= 0 and policy_idx < len(cell_texts):
                setting_name = cell_texts[policy_idx]
            elif len(cell_texts) > 0:
                # Default to first column if no policy column found
                setting_name = cell_texts[0]
            
            if state_idx >= 0 and state_idx < len(cell_texts):
                state = self._parse_state(cell_texts[state_idx])
            
            if value_idx >= 0 and value_idx < len(cell_texts):
                value = cell_texts[value_idx]
            
            # Handle 2-column format (Policy | Setting) - common in Microsoft reports
            # where 'setting' column contains both state and value
            if state_idx < 0 and value_idx >= 0 and value_idx < len(cell_texts):
                value_text = cell_texts[value_idx]
                # Check if value contains state indicator
                state, value = self._extract_state_from_value(value_text)
                
        else:
            # No headers - assume positional
            setting_name = cell_texts[0] if len(cell_texts) > 0 else ""
            if len(cell_texts) > 1:
                # Check if second column looks like a pure state
                second_col = cell_texts[1].lower().strip()
                if second_col in ['enabled', 'disabled', 'not configured']:
                    state = self._parse_state(cell_texts[1])
                    if len(cell_texts) > 2 and cell_texts[2]:
                        value = cell_texts[2]
                else:
                    # Try to extract state from value text
                    state, value = self._extract_state_from_value(cell_texts[1])
                    # If we have a 3rd column and no value extracted, use it
                    if not value and len(cell_texts) > 2 and cell_texts[2]:
                        value = cell_texts[2]
        
        if not setting_name:
            return None
        
        return PolicySetting(
            gpo_id=gpo_id,
            gpo_name=gpo_name,
            category=category,
            name=setting_name,
            state=state,
            value=value,
            scope=scope
        )
    
    def _extract_state_from_value(self, value_text: str) -> tuple[PolicyState, Optional[str]]:
        """Extract state and remaining value from a combined value text.
        
        Microsoft GPO HTML often puts both state and value in one column,
        e.g., "Enabled", "8 characters", "Disabled", "24 passwords remembered"
        
        Returns:
            Tuple of (PolicyState, remaining value or None)
        """
        if not value_text:
            return PolicyState.NOT_CONFIGURED, None
        
        text_lower = value_text.lower().strip()
        
        # Pure state values
        if text_lower == 'enabled':
            return PolicyState.ENABLED, None
        elif text_lower == 'disabled':
            return PolicyState.DISABLED, None
        elif text_lower in ['not configured', 'not defined']:
            return PolicyState.NOT_CONFIGURED, None
        
        # Value text that implies enabled state (contains a configured value)
        # Examples: "8 characters", "90 days", "24 passwords remembered"
        if value_text and value_text.strip():
            # If it has a numeric value or specific setting, it's configured (enabled)
            return PolicyState.ENABLED, value_text.strip()
        
        return PolicyState.NOT_CONFIGURED, None
    
    def _parse_xml(self, content: str, source_file: str) -> tuple[list[GPOInfo], list[PolicySetting]]:
        """Parse XML format GPO report (Get-GPOReport -ReportType XML or gpresult /X)."""
        gpos = []
        settings = []
        
        try:
            # Parse XML with lxml for namespace support
            root = etree.fromstring(content.encode('utf-8'))
            
            # Handle different XML namespaces
            nsmap = root.nsmap.copy()
            ns_default = nsmap.get(None, '')
            
            # Create namespace prefix for xpath
            ns = {'gp': ns_default} if ns_default else {}
            
            # Try to find GPO elements
            gpo_elements = root.xpath('//gp:GPO', namespaces=ns) if ns else root.findall('.//GPO')
            
            if not gpo_elements:
                # Try without namespace
                gpo_elements = root.findall('.//GPO')
            
            if not gpo_elements:
                # Single GPO report format
                gpo_info, gpo_settings = self._parse_single_gpo_xml(root, ns, source_file)
                if gpo_info:
                    gpos.append(gpo_info)
                    settings.extend(gpo_settings)
            else:
                for gpo_elem in gpo_elements:
                    gpo_info, gpo_settings = self._parse_gpo_element_xml(gpo_elem, ns, source_file)
                    if gpo_info:
                        gpos.append(gpo_info)
                        settings.extend(gpo_settings)
            
        except etree.XMLSyntaxError as e:
            logger.error(f"XML parsing error in '{source_file}': {e}")
        
        logger.info(f"Parsed XML file '{source_file}': {len(gpos)} GPO(s), {len(settings)} setting(s)")
        return gpos, settings
    
    def _parse_single_gpo_xml(self, root, ns: dict, source_file: str) -> tuple[Optional[GPOInfo], list[PolicySetting]]:
        """Parse a single GPO from XML root."""
        # Extract GPO name
        name_elem = self._find_element(root, ['Name', 'GPOName', 'DisplayName'], ns)
        gpo_name = name_elem.text if name_elem is not None and name_elem.text else Path(source_file).stem
        
        # Extract GUID
        guid_elem = self._find_element(root, ['Identifier/Identifier', 'Id', 'GUID', 'UniqueId'], ns)
        gpo_id = guid_elem.text if guid_elem is not None and guid_elem.text else str(uuid.uuid4())
        
        gpo_info = GPOInfo(
            id=gpo_id,
            name=gpo_name,
            source_file=source_file
        )
        
        # Extract additional metadata
        domain_elem = self._find_element(root, ['Domain', 'DomainName'], ns)
        if domain_elem is not None and domain_elem.text:
            gpo_info.domain = domain_elem.text
        
        created_elem = self._find_element(root, ['CreatedTime', 'WhenCreated'], ns)
        if created_elem is not None and created_elem.text:
            gpo_info.created = self._parse_datetime(created_elem.text)
        
        modified_elem = self._find_element(root, ['ModifiedTime', 'WhenChanged'], ns)
        if modified_elem is not None and modified_elem.text:
            gpo_info.modified = self._parse_datetime(modified_elem.text)
        
        # Extract settings
        settings = self._extract_settings_xml(root, ns, gpo_id, gpo_name)
        
        return gpo_info, settings
    
    def _parse_gpo_element_xml(self, gpo_elem, ns: dict, source_file: str) -> tuple[Optional[GPOInfo], list[PolicySetting]]:
        """Parse a GPO element from XML."""
        return self._parse_single_gpo_xml(gpo_elem, ns, source_file)
    
    def _find_element(self, parent, paths: list[str], ns: dict):
        """Find element using multiple possible paths."""
        for path in paths:
            # 1. Try strict namespace if provided
            if ns:
                try:
                    # Add namespace prefix to each path component
                    ns_path = '/'.join(f"gp:{p}" for p in path.split('/'))
                    result = parent.xpath(ns_path, namespaces=ns)
                    if result:
                        return result[0]
                except Exception:
                    pass
            
            # 2. Try standard find (for no namespace or simple cases)
            result = parent.find(f'.//{path}')
            if result is not None:
                return result
                
            # 3. Fallback: Try loose local-name matching for single-level paths
            # This handles cases where namespaces are messed up or unexpected
            if '/' not in path:
                child = self._find_child_by_local_name(parent, [path])
                if child is not None:
                    return child
                    
        return None
    
    def _extract_settings_xml(self, root, ns: dict, gpo_id: str, gpo_name: str) -> list[PolicySetting]:
        """Extract policy settings from XML structure."""
        settings = []
        
        # Look for Computer and User configurations
        for config_type, scope in [('Computer', 'Computer'), ('User', 'User')]:
            config_elem = self._find_element(root, [f'{config_type}', f'{config_type}Configuration'], ns)
            if config_elem is None:
                continue
            
            # Recursively find all policy settings
            settings.extend(self._extract_policy_nodes_xml(config_elem, gpo_id, gpo_name, scope, ""))
        
        return settings
    
    def _extract_policy_nodes_xml(
        self, 
        element, 
        gpo_id: str, 
        gpo_name: str, 
        scope: str, 
        category_path: str
    ) -> list[PolicySetting]:
        """Recursively extract policy nodes from XML."""
        settings = []
        
        for child in element:
            # Get local tag name (ignore namespace)
            tag_name = self._get_local_tag(child.tag)
            
            # Build category path
            current_category = f"{category_path}/{tag_name}" if category_path else tag_name
            
            # Check if this child ITSELF is a setting (has Name/SettingName property)
            # We look for DIRECT children with these names to avoid finding nested settings
            name_elem = self._find_child_by_local_name(child, ['Name', 'SettingName'])
            
            if name_elem is not None and name_elem.text:
                # It's a setting!
                state_elem = self._find_child_by_local_name(child, ['State', 'Enabled'])
                value_elem = self._find_child_by_local_name(child, ['Value', 'Data'])
                
                state = PolicyState.NOT_CONFIGURED
                if state_elem is not None and state_elem.text:
                    state = self._parse_state(state_elem.text)
                
                value = value_elem.text if value_elem is not None else None
                
                # Look for registry path
                reg_path = None
                reg_value = None
                
                # Check RegistryValue container
                reg_elem = self._find_child_by_local_name(child, ['RegistryValue'])
                if reg_elem is not None:
                    # Registry info might be in attributes or children
                    reg_path = reg_elem.get('path')
                    reg_value = reg_elem.get('valueName')
                    
                    if not reg_path:
                        kp = self._find_child_by_local_name(reg_elem, ['KeyPath'])
                        if kp is not None: reg_path = kp.text
                        
                    if not reg_value:
                        vn = self._find_child_by_local_name(reg_elem, ['ValueName'])
                        if vn is not None: reg_value = vn.text
                
                settings.append(PolicySetting(
                    gpo_id=gpo_id,
                    gpo_name=gpo_name,
                    category=category_path or "General", # Use parent path as category
                    name=name_elem.text,
                    state=state,
                    value=value,
                    registry_path=reg_path,
                    registry_value=reg_value,
                    scope=scope
                ))
            
            # Recurse into children to find more settings
            # (A setting node might also contain other settings in some schemas, 
            # or it might be a container like 'ExtensionData' that isn't a setting itself)
            settings.extend(self._extract_policy_nodes_xml(
                child, gpo_id, gpo_name, scope, current_category
            ))
        
        return settings

    def _get_local_tag(self, tag: str) -> str:
        """Strip namespace from tag."""
        if '}' in tag:
            return tag.split('}')[-1]
        return tag

    def _find_child_by_local_name(self, element, local_names: list[str]):
        """Find a direct child with a matching local tag name (ignoring namespace)."""
        for child in element:
            if self._get_local_tag(child.tag) in local_names:
                return child
        return None
    
    def _parse_state(self, state_str: str) -> PolicyState:
        """Parse a state string to PolicyState enum."""
        state_lower = state_str.lower().strip()
        if state_lower in ['enabled', 'true', '1', 'yes', 'on']:
            return PolicyState.ENABLED
        elif state_lower in ['disabled', 'false', '0', 'no', 'off']:
            return PolicyState.DISABLED
        return PolicyState.NOT_CONFIGURED
    
    def _parse_datetime(self, dt_str: str) -> Optional[datetime]:
        """Parse various datetime formats."""
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %I:%M:%S %p',
            '%d/%m/%Y %H:%M:%S',
            '%B %d, %Y %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        
        # Try parsing with dateutil as fallback
        try:
            from dateutil.parser import parse
            return parse(dt_str)
        except Exception:
            return None


# Convenience function for parsing multiple files
def parse_gpo_files(file_paths: list[Path]) -> tuple[list[GPOInfo], list[PolicySetting]]:
    """Parse multiple GPO export files."""
    parser = GPOParser()
    all_gpos = []
    all_settings = []
    
    for path in file_paths:
        gpos, settings = parser.parse_file(path)
        all_gpos.extend(gpos)
        all_settings.extend(settings)
    
    return all_gpos, all_settings
