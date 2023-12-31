COPY pilot_casbin.casbin_rule (ptype, v0, v1, v2, v3, v4, v5) FROM stdin;
p	admin	*	announcement	create	pilotdefault	\N
p	admin	core	collections	manage	pilotdefault	\N
p	collaborator	core	collections	manage	pilotdefault	\N
p	admin	greenroom	copyrequest	manage	pilotdefault	\N
p	collaborator	greenroom	copyrequest_in_own_namefolder	create	pilotdefault	\N
p	admin	core	file_any	view	pilotdefault	\N
p	admin	core	file_any	upload	pilotdefault	\N
p	admin	core	file_any	download	pilotdefault	\N
p	admin	core	file_any	delete	pilotdefault	\N
p	admin	core	file_any	copy	pilotdefault	\N
p	admin	greenroom	file_any	view	pilotdefault	\N
p	admin	greenroom	file_any	upload	pilotdefault	\N
p	admin	greenroom	file_any	download	pilotdefault	\N
p	admin	greenroom	file_any	delete	pilotdefault	\N
p	admin	greenroom	file_any	copy	pilotdefault	\N
p	admin	core	file_in_own_namefolder	view	pilotdefault	\N
p	admin	core	file_in_own_namefolder	upload	pilotdefault	\N
p	admin	core	file_in_own_namefolder	download	pilotdefault	\N
p	admin	core	file_in_own_namefolder	delete	pilotdefault	\N
p	admin	core	file_in_own_namefolder	copy	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	view	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	upload	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	download	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	delete	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	copy	pilotdefault	\N
p	collaborator	core	file_any	view	pilotdefault	\N
p	collaborator	core	file_any	upload	pilotdefault	\N
p	collaborator	core	file_any	download	pilotdefault	\N
p	collaborator	core	file_any	delete	pilotdefault	\N
p	collaborator	core	file_in_own_namefolder	view	pilotdefault	\N
p	collaborator	core	file_in_own_namefolder	upload	pilotdefault	\N
p	collaborator	core	file_in_own_namefolder	download	pilotdefault	\N
p	collaborator	core	file_in_own_namefolder	delete	pilotdefault	\N
p	collaborator	greenroom	file_in_own_namefolder	view	pilotdefault	\N
p	collaborator	greenroom	file_in_own_namefolder	upload	pilotdefault	\N
p	collaborator	greenroom	file_in_own_namefolder	download	pilotdefault	\N
p	collaborator	greenroom	file_in_own_namefolder	delete	pilotdefault	\N
p	contributor	greenroom	file_in_own_namefolder	view	pilotdefault	\N
p	contributor	greenroom	file_in_own_namefolder	upload	pilotdefault	\N
p	contributor	greenroom	file_in_own_namefolder	download	pilotdefault	\N
p	contributor	greenroom	file_in_own_namefolder	delete	pilotdefault	\N
p	admin	*	invitation	manage	pilotdefault	\N
p	admin	*	resource_request	create	pilotdefault	\N
p	collaborator	*	resource_request	create	pilotdefault	\N
p	admin	*	resource_request	manage	pilotdefault	\N
p	admin	core	tag	manage	pilotdefault	\N
p	admin	greenroom	tag	manage	pilotdefault	\N
p	collaborator	core	tag	manage	pilotdefault	\N
p	collaborator	greenroom	tag	manage	pilotdefault	\N
p	contributor	greenroom	tag	manage	pilotdefault	\N
p	admin	*	users	view	pilotdefault	\N
p	admin	*	workbench	manage	pilotdefault	\N
p	admin	*	workbench	view	pilotdefault	\N
p	collaborator	*	workbench	view	pilotdefault	\N
p	contributor	*	workbench	view	pilotdefault	\N
p	admin	*	users	manage	pilotdefault	\N
p	platform_admin	*	notification	manage	pilotdefault	\N
p	admin	*	project	view	pilotdefault	\N
p	contributor	*	project	view	pilotdefault	\N
p	collaborator	*	project	view	pilotdefault	\N
p	admin	*	project	update	pilotdefault	\N
p	platform_admin	*	project	create	pilotdefault	\N
p	platform_admin	*	workbench	manage	pilotdefault	\N
p	admin	*	file_attribute_template	manage	pilotdefault	\N
p	admin	greenroom	file_any	annotate	pilotdefault	\N
p	admin	core	file_any	annotate	pilotdefault	\N
p	admin	greenroom	file_in_own_namefolder	annotate	pilotdefault	\N
p	admin	core	file_in_own_namefolder	annotate	pilotdefault	\N
p	collaborator	core	file_any	annotate	pilotdefault	\N
p	collaborator	greenroom	file_in_own_namefolder	annotate	pilotdefault	\N
p	collaborator	core	file_in_own_namefolder	annotate	pilotdefault	\N
\.
