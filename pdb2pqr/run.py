"""Routines for running the code with a given set of options and PDB files."""
import logging
import time
import io
import os.path
from . import utilities
from . import definitions
from . import protein
from . import routines
from . import hydrogens
from . import forcefield
from . import aa
from . import na
from . import pdb
from .pdb2pka.ligandclean import ligff
from . import __version__


_LOGGER = logging.getLogger(__name__)


def get_old_header(pdblist):
    """Get old header from list of PDBs.

    Args:
        pdblist:  list of PDBs
    Returns:
        Old header as string.
    """
    old_header = io.StringIO()
    header_types = (pdb.HEADER, pdb.TITLE, pdb.COMPND, pdb.SOURCE, pdb.KEYWDS,
                    pdb.EXPDTA, pdb.AUTHOR, pdb.REVDAT, pdb.JRNL, pdb.REMARK,
                    pdb.SPRSDE, pdb.NUMMDL)
    for pdb_obj in pdblist:
        if not isinstance(pdb_obj, header_types):
            break
        old_header.write(str(pdb_obj))
        old_header.write('\n')
    return old_header.getvalue()


def print_pqr_header_cif(atomlist, reslist, charge, force_field,
                         ph_calc_method, ph, ffout, include_old_header=False):
    """Print the header for the PQR file in cif format.

    Args:
        atomlist: A list of atoms that were unable to have charges assigned (list)
        reslist:  A list of residues with non-integral charges (list)
        charge:  The total charge on the protein (float)
        force_field:  The forcefield name (string)
        ph:  pH value, if any. (float)
        ffout:  ff used for naming scheme (string)
    Returns
        header:  The header for the PQR file (string)
    """
    if force_field is None:
        force_field = "User force field"
    else:
        force_field = force_field.upper()

    header = "#\n"
    header += "loop_\n"
    header += "_pdbx_database_remark.id\n"
    header += "_pdbx_database_remark.text\n"
    header += "1\n"
    header += ";\n"
    header += "PQR file generated by PDB2PQR (Version %s)\n" % __version__
    header += "\n"
    header += "Forcefiled used: %s\n" % force_field
    if ffout is not None:
        header += "Naming scheme used: %s\n" % ffout
    header += "\n"
    if ph_calc_method is not None:
        header += "pKas calculated by %s and assigned using pH %.2f\n" % (ph_calc_method,
                                                                          ph)
    header += ";\n"
    header += "2\n"
    header += ";\n"
    if len(atomlist) > 0:
        header += "Warning: PDB2PQR was unable to assign charges\n"
        header += "to the following atoms (omitted below):\n"
        for atom in atomlist:
            header += "             %i %s in %s %i\n" % (atom.get("serial"),
                                                         atom.get("name"),
                                                         atom.get("residue").get("name"),
                                                         atom.get("residue").get("res_seq"))
        header += "This is usually due to the fat thtat this residue is not\n"
        header += "an amino acid or nucleic acid; or, there are no parameters\n"
        header += "available for the specific protonation state of this\n"
        header += "residue in the selected forcefield.\n"
    if len(reslist) > 0:
        header += "\n"
        header += "Warning: Non-integral net charges were found in\n"
        header += "the following residues:\n"
        for residue in reslist:
            header += "              %s - Residue Charge: %.4f\n" % (residue,
                                                                     residue.get_charge())
    header += ";\n"
    header += "3\n"
    header += ";\n"
    header += "Total charge on this protein: %.4f e\n" % charge
    header += ";\n"
    if include_old_header:
        header += "4\n"
        header += ";\n"
        header += "Including original cif header is not implemented yet.\n"
        header += ";\n"
    header += "#\n"
    header += "loop_\n"
    header += "_atom_site.group_PDB\n"
    header += "_atom_site.id\n"
    header += "_atom_site.label_atom_id\n"
    header += "_atom_site.label_comp_id\n"
    header += "_atom_site.label_seq_id\n"
    header += "_atom_site.Cartn_x\n"
    header += "_atom_site.Cartn_y\n"
    header += "_atom_site.Cartn_z\n"
    header += "_atom_site.pqr_partial_charge\n"
    header += "_atom_site.pqr_radius\n"
    return header


def print_pqr_header(pdblist, atomlist, reslist, charge, force_field, ph_calc_method,
                     ph, ffout, include_old_header=False):
    """Print the header for the PQR file

    Args:
        atomlist: A list of atoms that were unable to have charges assigned (list)
        reslist:  A list of residues with non-integral charges (list)
        charge:  The total charge on the protein (float)
        ff:  The forcefield name (string)
        ph:  pH value, if any. (float)
        ffout:  ff used for naming scheme (string)
    Returns
        header:  The header for the PQR file (string)
    """
    if force_field is None:
        force_field = 'User force field'
    else:
        force_field = force_field.upper()
    header = "REMARK   1 PQR file generated by PDB2PQR (Version %s)\n" % __version__
    header = header + "REMARK   1\n"
    header = header + "REMARK   1 Forcefield Used: %s\n" % force_field
    if not ffout is None:
        header = header + "REMARK   1 Naming Scheme Used: %s\n" % ffout
    header = header + "REMARK   1\n"

    if ph_calc_method is not None:
        header = header + ("REMARK   1 pKas calculated by %s and assigned "
                           "using pH %.2f\n") % (ph_calc_method, ph)
        header = header + "REMARK   1\n"

    if len(atomlist) != 0:
        header += "REMARK   5 WARNING: PDB2PQR was unable to assign charges\n"
        header += "REMARK   5          to the following atoms (omitted below):\n"
        for atom in atomlist:
            header += "REMARK   5              %i %s in %s %i\n" % \
                      (atom.get("serial"), atom.get("name"), \
                       atom.get("residue").get("name"), \
                       atom.get("residue").get("res_seq"))
        header += "REMARK   5 This is usually due to the fact that this residue is not\n"
        header += "REMARK   5 an amino acid or nucleic acid; or, there are no parameters\n"
        header += "REMARK   5 available for the specific protonation state of this\n"
        header += "REMARK   5 residue in the selected forcefield.\n"
        header += "REMARK   5\n"
    if len(reslist) != 0:
        header += "REMARK   5 WARNING: Non-integral net charges were found in\n"
        header += "REMARK   5          the following residues:\n"
        for residue in reslist:
            header += "REMARK   5              %s - Residue Charge: %.4f\n" % \
                      (residue, residue.get_charge())
        header += "REMARK   5\n"
    header += "REMARK   6 Total charge on this protein: %.4f e\n" % charge
    header += "REMARK   6\n"

    if include_old_header:
        header += "REMARK   7 Original PDB header follows\n"
        header += "REMARK   7\n"
        header += get_old_header(pdblist)
    return header


def run_pdb2pqr(pdblist, options):
    """Run the PDB2PQR Suite

    Args:
        pdblist: The list of objects that was read from the PDB file given as
                 input (list)
        options: The name of the forcefield (string)

    Returns
        A dictionary with the following elements:
        * header:  The PQR file header (string)
        * lines:  The PQR file atoms (list)
        * missed_ligands:  A list of ligand residue names whose charges could
                           not be assigned (ligand)
        * protein:  The protein object
    """
    pkaname = ""
    lines = []
    ligand = None
    atomcount = 0   # Count the number of ATOM records in pdb
    outroot = utilities.getPQRBaseFileName(options.output_pqr)

    if options.pka_method == 'propka':
        pkaname = outroot + ".propka"
        #TODO: What? Shouldn't it be up to propka on how to handle this?
        if os.path.isfile(pkaname):
            os.remove(pkaname)

    start = time.time()
    _LOGGER.info("Beginning PDB2PQR...")

    my_definition = definitions.Definition()
    _LOGGER.info("Parsed Amino Acid definition file.")

    if options.drop_water:
        # Remove the waters
        pdblist_new = []
        for record in pdblist:
            if isinstance(record, (pdb.HETATM, pdb.ATOM, pdb.SIGATM,
                                   pdb.SEQADV)):
                if record.res_name in aa.WAT.water_residue_names:
                    continue
            pdblist_new.append(record)

        pdblist = pdblist_new

    # Check for the presence of a ligand!  This code is taken from pdb2pka/pka.py
    if options.ligand is not None:
        my_protein, my_definition, ligand = ligff.initialize(my_definition,
                                                             options.ligand,
                                                             pdblist)
        for atom in my_protein.get_atoms():
            if atom.type == "ATOM":
                atomcount += 1
    else:
        my_protein = protein.Protein(pdblist, my_definition)

    _LOGGER.info("Created protein object:")
    _LOGGER.info("  Number of residues in protein: %s", my_protein.num_residues())
    _LOGGER.info("  Number of atoms in protein   : %s", my_protein.num_atoms())

    my_routines = routines.Routines(my_protein)
    for residue in my_protein.get_residues():
        multoccupancy = 0
        for atom in residue.get_atoms():
            if atom.alt_loc != "":
                multoccupancy = 1
                txt = "Warning: multiple occupancies found: %s in %s." % (atom.name,
                                                                          residue)
                _LOGGER.warn(txt)
        if multoccupancy == 1:
            _LOGGER.warn(("WARNING: multiple occupancies found in %s at least "
                          "one of the instances is being ignored."), residue)

    my_routines.set_termini(options.neutraln, options.neutralc)
    my_routines.update_bonds()

    if options.clean:
        header = ""
        lines = my_protein.print_atoms(my_protein.get_atoms(), options.chain)

        # Process the extensions
        # TODO - extension handling is messed up.
        for ext in options.active_extensions:
            _LOGGER.error("Ignoring extension: %s", ext)
            # module = extensions.extDict[ext]
            # module.run_extension(my_routines, outroot, extensionOptions)

        _LOGGER.debug("Total time taken: %.2f seconds", (time.time() - start))

        #Be sure to include None for missed ligand residues
        results_dict = {"header": header, "lines": lines,
                        "missed_ligands": None, "protein": my_protein}
        return results_dict

    #remove any future need to convert to lower case
    if options.userff is not None:
        force_field = options.userff.lower()
    elif options.ff is not None:
        force_field = options.ff.lower()
    if options.ffout is not None:
        ffout = options.ffout.lower()

    if not options.assign_only:
        # It is OK to process ligands with no ATOM records in the pdb
        if atomcount == 0 and ligand is not None:
            pass
        else:
            my_routines.find_missing_heavy()
        my_routines.update_ss_bridges()

        if options.debump:
            my_routines.debump_protein()

        # TODO - both PROPKA and PDB2PKA are messed up
        if options.pka_method == 'propka':
            raise NotImplementedError("PROPKA is broken.")
            # my_routines.run_propka(options.ph, options.ff, ph_calc_options, version=31)
        elif options.pka_method == 'pdb2pka':
            raise NotImplementedError("PROPKA is broken.")
            # my_routines.run_pdb2pka(options.ph, options.ff, pdblist, ligand, ph_calc_options)

        my_routines.add_hydrogens()
        my_hydrogen_routines = hydrogens.HydrogenRoutines(my_routines)

        if options.debump:
            my_routines.debump_protein()

        if options.opt:
            my_hydrogen_routines.set_optimizeable_hydrogens()
            my_routines.hold_residues(None)
            my_hydrogen_routines.initialize_full_optimization()
            my_hydrogen_routines.optimize_hydrogens()
        else:
            my_hydrogen_routines.initialize_wat_optimization()
            my_hydrogen_routines.optimize_hydrogens()

        # Special for GLH/ASH, since both conformations were added
        my_hydrogen_routines.cleanup()

    else:  # Special case for HIS if using assign-only
        for residue in my_protein.get_residues():
            if isinstance(residue, aa.HIS):
                my_routines.apply_patch("HIP", residue)

    my_routines.set_states()
    my_forcefield = forcefield.Forcefield(force_field, my_definition, options.userff,
                                          options.usernames)
    hitlist, misslist = my_routines.apply_force_field(my_forcefield)

    ligsuccess = 0
    if options.ligand is not None:
        # If this is independent, we can assign charges and radii here
        for residue in my_protein.get_residues():
            if isinstance(residue, aa.LIG):
                templist = []
                ligand.make_up2date(residue)
                for atom in residue.get_atoms():
                    atom.ffcharge = ligand.ligand_props[atom.name]["charge"]
                    atom.radius = ligand.ligand_props[atom.name]["radius"]
                    if atom in misslist:
                        misslist.pop(misslist.index(atom))
                        templist.append(atom)

                charge = residue.get_charge()
                if abs(charge - int(charge)) > 0.001:
                    # Ligand parameterization failed
                    _LOGGER.warn(("WARNING: PDB2PQR could not successfully "
                                  "parameterize the desired ligand; it has "
                                  "been left out of the PQR file."))

                    # remove the ligand
                    my_protein.residues.remove(residue)
                    for my_chain in my_protein.chains:
                        if residue in my_chain.residues:
                            my_chain.residues.remove(residue)
                else:
                    ligsuccess = 1
                    # Mark these atoms as hits
                    hitlist = hitlist + templist

    # Temporary fix; if ligand was successful, pull all ligands from misslist
    if ligsuccess:
        templist = misslist[:]
        for atom in templist:
            if isinstance(atom.residue, (aa.Amino, na.Nucleic)):
                continue
            misslist.remove(atom)

    # Create the Typemap
    if options.typemap:
        typemapname = "%s-typemap.html" % outroot
        my_protein.create_html_typemap(my_definition, typemapname)

    # Grab the protein charge
    reslist, charge = my_protein.get_charge()

    # If we want a different naming scheme, use that
    if options.ffout is not None:
        scheme = ffout
        userff = None # Currently not supported
        if scheme != force_field:
            my_name_scheme = forcefield.Forcefield(scheme, my_definition, userff)
        else:
            my_name_scheme = my_forcefield
        my_routines.apply_name_scheme(my_name_scheme)

    if options.is_cif:
        header = print_pqr_header_cif(misslist, reslist, charge, force_field,
                                      options.pka_method, options.ph, options.ffout,
                                      include_old_header=options.include_header)
    else:
        header = print_pqr_header(pdblist, misslist, reslist, charge, force_field,
                                  options.pka_method, options.ph, options.ffout,
                                  include_old_header=options.include_header)

    lines = my_protein.print_atoms(hitlist, options.chain)

    # Determine if any of the atoms in misslist were ligands
    missedligandresidues = []
    for atom in misslist:
        if isinstance(atom.residue, (aa.Amino, na.Nucleic)):
            continue
        if atom.res_name not in missedligandresidues:
            missedligandresidues.append(atom.res_name)

    # Process the extensions
    # TODO - extensions are messed up
    for ext in options.active_extensions:
        _LOGGER.error("Unable to run extension: %s", ext)
        # module = extensions.extDict[ext]
        # module.run_extension(my_routines, outroot, extensionOptions)
    _LOGGER.debug("Total time taken: %.2f seconds", (time.time() - start))
    result_dict = {}
    result_dict["header"] = header
    result_dict["lines"] = lines
    result_dict["missed_ligands"] = missedligandresidues
    result_dict["protein"] = my_protein
    return result_dict
