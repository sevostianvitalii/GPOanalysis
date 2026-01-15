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
        content = file_path.read_text(encoding='utf-8', errors='replace')
        
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
    
    def _extract_settings_html(self, soup: BeautifulSoup, gpo_id: str, gpo_name: str) -> list[PolicySetting]:
        """Extract policy settings from HTML tables."""
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
        """Parse a table row as a policy setting."""
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
        
        if headers:
            for i, header in enumerate(headers):
                if i < len(cell_texts):
                    if 'policy' in header or 'setting' in header or 'name' in header:
                        setting_name = cell_texts[i]
                    elif 'state' in header or 'status' in header:
                        state = self._parse_state(cell_texts[i])
                    elif 'value' in header or 'data' in header:
                        value = cell_texts[i]
        else:
            # Assume first column is name, second is state/value
            setting_name = cell_texts[0] if len(cell_texts) > 0 else ""
            if len(cell_texts) > 1:
                # Check if second column looks like a state
                second_col = cell_texts[1].lower()
                if second_col in ['enabled', 'disabled', 'not configured']:
                    state = self._parse_state(cell_texts[1])
                    if len(cell_texts) > 2:
                        value = cell_texts[2]
                else:
                    value = cell_texts[1]
        
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
