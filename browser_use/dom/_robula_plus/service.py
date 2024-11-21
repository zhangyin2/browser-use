import re
from typing import List, Optional

from bs4 import BeautifulSoup, Tag


class RobulaPlusOptions:
	def __init__(
		self,
		attribute_prioritization_list: Optional[List[str]] = None,
		attribute_blacklist: Optional[List[str]] = None,
	):
		self.attribute_prioritization_list: List[str] = attribute_prioritization_list or [
			'name',
			'title',
			'alt',
			'value',
		]
		self.attribute_blacklist: List[str] = attribute_blacklist or [
			'href',
			'class',
			'src',
			'onclick',
			'onload',
			'tabindex',
			'width',
			'height',
			'style',
			'size',
			'maxlength',
		]


class XPath:
	def __init__(self, value: str) -> None:
		self.value: str = value

	def get_value(self) -> str:
		return self.value

	def starts_with(self, prefix: str) -> bool:
		return self.value.startswith(prefix)

	def substring(self, start: int) -> str:
		return self.value[start:]

	def head_has_any_predicates(self) -> bool:
		return '[' in self.value.split('/')[2]

	def head_has_position_predicate(self) -> bool:
		head = self.value.split('/')[2]
		return 'position()' in head or 'last()' in head or bool(re.search(r'\[\d+\]', head))

	def head_has_text_predicate(self) -> bool:
		return 'text()' in self.value.split('/')[2]

	def add_predicate_to_head(self, predicate: str) -> None:
		parts = self.value.split('/')
		parts[2] += predicate
		self.value = '/'.join(parts)

	def get_length(self) -> int:
		return len([part for part in self.value.split('/') if part])


class RobulaPlus:
	def __init__(self, options: Optional[RobulaPlusOptions] = None):
		if options is None:
			options = RobulaPlusOptions()
		self.attribute_prioritization_list = options.attribute_prioritization_list
		self.attribute_blacklist = options.attribute_blacklist

	def get_robust_xpath(self, soup: BeautifulSoup, element: Tag, current_xpath: str) -> str:
		"""Returns an optimized robust XPath locator string."""
		xpath_list: List[XPath] = [XPath('//*')]

		while xpath_list:
			xpath = xpath_list.pop(0)
			print(f'Current XPath: {xpath.get_value()}')
			temp: List[XPath] = []

			# Apply transformations
			temp.extend(self.transf_convert_star(xpath, element))
			temp.extend(self.transf_add_id(xpath, element))
			temp.extend(self.transf_add_text(xpath, element))
			temp.extend(self.transf_add_attribute(xpath, element))
			temp.extend(self.transf_add_attribute_set(xpath, element))
			temp.extend(self.transf_add_position(xpath, element, soup))
			temp.extend(self.transf_add_level(xpath, element))

			# Remove duplicates
			temp = list({x.get_value(): x for x in temp}.values())

			for x in temp:
				if self.uniquely_locate(x.get_value(), element, soup):
					return x.get_value()
				xpath_list.append(x)

		raise RuntimeError('Failed to generate robust XPath')

	def uniquely_locate(self, xpath: str, target_element: Tag, soup: BeautifulSoup) -> bool:
		"""Determines whether an XPath uniquely identifies the given element."""
		try:
			# Using bs4's select with a CSS selector converted from XPath
			elements = soup.select(self.xpath_to_css(xpath))
			return len(elements) == 1 and elements[0] is target_element
		except Exception:
			return False

	def get_ancestor(self, element: Tag, index: int) -> Tag:
		"""Gets the ancestor element at the specified index."""
		current = element
		for _ in range(index):
			parent = current.parent
			if not parent or not isinstance(parent, Tag):
				raise ValueError('Ancestor index out of bounds')
			current = parent
		return current

	def get_ancestor_count(self, element: Tag) -> int:
		"""Gets the number of ancestors for the element."""
		count = 0
		current = element
		while True:
			parent = current.parent
			if not parent or not isinstance(parent, Tag):
				break
			count += 1
			current = parent
		return count

	def transf_convert_star(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Transforms * to specific tag name."""
		output: List[XPath] = []
		if xpath.starts_with('//*'):
			tag_name = element.name.lower()
			output.append(XPath('//' + tag_name + xpath.substring(3)))
		return output

	def transf_add_id(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Adds ID predicate if available."""
		output: List[XPath] = []
		if 'id' in element.attrs and not xpath.head_has_any_predicates():
			new_xpath = XPath(xpath.get_value())
			new_xpath.add_predicate_to_head(f"[@id='{element['id']}']")
			output.append(new_xpath)
		return output

	def transf_add_text(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Adds text predicate if available."""
		output: List[XPath] = []
		text_content = element.get_text(strip=True)
		if (
			text_content
			and not xpath.head_has_position_predicate()
			and not xpath.head_has_text_predicate()
		):
			new_xpath = XPath(xpath.get_value())
			new_xpath.add_predicate_to_head(f"[contains(text(),'{text_content}')]")
			output.append(new_xpath)
		return output

	def transf_add_attribute(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Adds attribute predicates."""
		output: List[XPath] = []
		if not xpath.head_has_any_predicates():
			# Add priority attributes first
			for attr_name in self.attribute_prioritization_list:
				if attr_name in element.attrs:
					new_xpath = XPath(xpath.get_value())
					new_xpath.add_predicate_to_head(f"[@{attr_name}='{element[attr_name]}']")
					output.append(new_xpath)

			# Add remaining non-blacklisted attributes
			for attr_name, attr_value in element.attrs.items():
				if (
					attr_name not in self.attribute_blacklist
					and attr_name not in self.attribute_prioritization_list
				):
					new_xpath = XPath(xpath.get_value())
					new_xpath.add_predicate_to_head(f"[@{attr_name}='{attr_value}']")
					output.append(new_xpath)
		return output

	def transf_add_position(self, xpath: XPath, element: Tag, soup: BeautifulSoup) -> List[XPath]:
		"""Adds position predicate."""
		output: List[XPath] = []
		if not xpath.head_has_position_predicate():
			parent = element.parent
			if parent:
				if xpath.starts_with('//*'):
					position = 1 + len([s for s in element.previous_siblings if isinstance(s, Tag)])
				else:
					position = 1 + len(
						[
							s
							for s in element.previous_siblings
							if isinstance(s, Tag) and s.name == element.name
						]
					)
				new_xpath = XPath(xpath.get_value())
				new_xpath.add_predicate_to_head(f'[{position}]')
				output.append(new_xpath)
		return output

	def transf_add_level(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Adds level transformation."""
		output: List[XPath] = []
		ancestor_count = self.get_ancestor_count(element)
		if xpath.get_length() - 1 < ancestor_count:
			output.append(XPath('//*' + xpath.substring(1)))
		return output

	def transf_add_attribute_set(self, xpath: XPath, element: Tag) -> List[XPath]:
		"""Adds attribute set predicates."""
		output: List[XPath] = []
		if not xpath.head_has_any_predicates():
			attributes = [
				{'name': name, 'value': value}
				for name, value in element.attrs.items()
				if name not in self.attribute_blacklist
			]

			power_set = self._generate_power_set(attributes)
			power_set = [s for s in power_set if len(s) >= 2]

			for attr_set in power_set:
				attr_set.sort(key=lambda x: self._get_attribute_priority(x['name']))
				predicate = self._create_attribute_set_predicate(attr_set)
				new_xpath = XPath(xpath.get_value())
				new_xpath.add_predicate_to_head(predicate)
				output.append(new_xpath)

		return output

	def _generate_power_set(self, attributes: List[dict]) -> List[List[dict]]:
		"""Generates power set of attributes."""
		result = [[]]
		for attr in attributes:
			result.extend([subset + [attr] for subset in result])
		return result

	def _get_attribute_priority(self, attr_name: str) -> int:
		"""Gets the priority of an attribute."""
		try:
			return self.attribute_prioritization_list.index(attr_name)
		except ValueError:
			return len(self.attribute_prioritization_list)

	def _create_attribute_set_predicate(self, attr_set: List[dict]) -> str:
		"""Creates an XPath predicate from an attribute set."""
		conditions = [f"@{attr['name']}='{attr['value']}'" for attr in attr_set]
		return f"[{' and '.join(conditions)}]"

	def xpath_to_css(self, xpath: str) -> str:
		"""Convert XPath to CSS selector for BS4 compatibility."""
		# This is a simplified conversion - you may need to expand it
		# based on your specific XPath patterns
		css = xpath.replace('//', ' ')
		css = re.sub(r'\[@([^=]+)=\'([^\']+)\'\]', r'[\1="\2"]', css)
		css = css.strip()
		return css
